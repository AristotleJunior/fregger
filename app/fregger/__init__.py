#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/2/24 13:07
# @Author  : Rain
# @Desc    : Automatically generate Swagger docs for Flask-Restful
# @File    : __init__.py.py

from flask_restful.reqparse import RequestParser
from flask_restful import Resource
from flask import request, Response, abort, current_app
from jinja2 import Template
import functools
import inspect
import re
import os


_root_path = os.path.dirname(os.path.abspath(__file__))


class _FreggerJSONResource(Resource):
    def get(self):
        if not current_app.config['DEBUG']:
            abort(404)

        url = request.path
        first = url.index('/')
        last = url.rindex('/')
        key = url[first:last]

        pool = Fregger.global_pool()
        return pool[key], 200, {'Access-Control-Allow-Origin': '*'}


class _FreggerHTMLResource(Resource):
    def get(self):
        if not current_app.config['DEBUG']:
            abort(404)

        with open(os.path.join(_root_path, 'static', 'index.html'), "r") as fs:
            template = Template(fs.read())
            mime = 'text/html'
        return Response(template.render(), mimetype=mime)


class _FreggerStaticResource(Resource):
    def get(self, file_path):
        if not current_app.config['DEBUG']:
            abort(404)

        mime = _convert_mime(file_path)

        full_path = os.path.join(_root_path, 'static', file_path)

        if os.path.exists(full_path):
            file = open(full_path, "rb")
            return Response(file, mimetype=mime)

        abort(404)


class Fregger(object):
    __global_pool = dict()

    def __init__(self, api, desc='', version='1.0', title='Fregger Title', host='localhost:5000', base_path=None, schemes=('http', 'https')):
        if not api:
            raise ValueError('api must be set.')

        self.__paths = dict()
        self.__definitions = dict()
        self.__end_point = dict()
        self.__end_point['paths'] = self.__paths

        self.__api = api
        api.add_resource(_FreggerJSONResource, '/fregger.json')
        api.add_resource(_FreggerHTMLResource, '/fregger.html')
        api.add_resource(_FreggerStaticResource, '/<path:file_path>')
        self.__origin_add_resource = api.add_resource
        api.add_resource = self.__add_resource

        info = dict()
        self.__end_point['swagger'] = '2.0'

        info['description'] = desc
        info['version'] = version
        info['title'] = title
        self.__end_point['info'] = info
        # tags = [{'name': 'all', 'description': title}]
        # self.__end_point['tags'] = tags
        self.__end_point['host'] = host
        self.__end_point['schemes'] = schemes
        if not base_path:
            base_path = api.prefix
        if api.blueprint:
            base_path = '/' + api.blueprint.name + base_path

        self.__end_point['basePath'] = base_path

        self.__global_pool[base_path] = self.__end_point

    @staticmethod
    def global_pool():
        return Fregger.__global_pool

    def __add_resource(self, resource, *urls, **kwargs):
        self.__origin_add_resource(resource, *urls, **kwargs)

        if resource.__name__ in self.__paths:
            url = urls[0]
            var_type = _convert_keyword(str.__name__)
            pattern = re.compile(r'(.*)(<((int|string|float):)?(\w+)>)(.*)')
            match = pattern.match(url)
            if match:
                prefix = match.group(1)
                suffix = match.group(6)
                var_type = _convert_keyword(match.group(4))
                var = match.group(5)
                url = prefix + '{' + var + '}' + suffix

            self.__paths[url] = self.__paths.pop(resource.__name__)

            methods = self.__paths[url]
            for params in methods.values():
                params = params.get('parameters')
                if params:
                    for param in params:
                        if param.get('in') == 'path':
                            param['type'] = var_type

    def generate_doc(self, parser=None, summary=None, tags=('ALL',)):
        parser_args = list()
        if parser:
            if not isinstance(parser, RequestParser):
                raise ValueError('Fregger argument should be None or instance of RequestParser')
            else:
                # parse request args, in: body
                for a in parser.args:
                    param = dict()
                    param['name'] = _convert_name_with_help(a.name, a.help)
                    param['in'] = _convert_keyword(a.location)
                    param['description'] = a.help or ''
                    param['type'] = _convert_keyword(a.type.__name__)
                    param['required'] = not a.nullable
                    if a.default:
                        param['default'] = _convert_keyword(a.default)
                    parser_args.append(param)

        def decorator(func):
            # parse path args from the method parameters, in: path
            parameters = inspect.signature(func).parameters
            keys = list(parameters.keys())[1:]

            cls_name = func.__qualname__.split('.')[0]

            if cls_name not in self.__paths:
                self.__paths[cls_name] = dict()

            methods = self.__paths[cls_name]
            if func.__name__ not in methods:
                methods[func.__name__] = dict()

            params = list()

            for k in keys:
                p = dict()
                p['in'] = 'path'
                p['name'] = k
                p['required'] = True
                p['type'] = _convert_keyword(str.__name__)
                params.append(p)

            params.extend(parser_args)

            body = dict()

            index = 0
            while index < len(params):
                p = params[index]
                if p['in'] == 'body':
                    name = p['name']
                    var_type = p['type']
                    body[name] = {'type': var_type}
                    params.pop(index)
                else:
                    index += 1

            if len(body) > 0:
                if not self.__end_point.get('definitions'):
                    self.__end_point['definitions'] = dict()

                definitions = self.__end_point['definitions']
                model_name = func.__qualname__.replace('.', '_')

                model = definitions[model_name] = dict()
                model['type'] = 'object'
                properties = model['properties'] = dict()
                for name, var_type in body.items():
                    properties[name] = var_type

                p = dict()
                p['in'] = 'body'
                p['name'] = 'body'
                p['description'] = 'some description'
                p['required'] = True
                p['schema'] = {"$ref": "#/definitions/" + model_name}
                params.append(p)

            if len(params) > 0:
                methods[func.__name__]['parameters'] = params

            if summary:
                methods[func.__name__]['summary'] = summary

            if isinstance(tags, (list, tuple)) and len(tags) > 0:
                methods[func.__name__]['tags'] = tags

            methods[func.__name__]['responses'] = {
                "200": {
                    "description": "Operation succeeded."
                },
                "400": {
                    "description": "Operation failed."
                }
            }

            @functools.wraps(func)
            def wrapper(*args, **kw):
                return func(*args, **kw)

            return wrapper

        return decorator


_mimes = {'gif': 'image/gif', 'png': 'image/png', 'js': 'text/javascript', 'css': 'text/css'}


def _convert_mime(file):
    extension = file.split('.')[-1]

    if extension in _mimes:
        return _mimes.get(extension)

    return 'text/plain'


_keywords_mapping = {'bool': 'boolean', 'str': 'string', 'int': 'integer', 'json': 'body', 'args': 'query'}


def _convert_keyword(word):

    if not word:
        return ''

    if word in _keywords_mapping:
        return _keywords_mapping[word]
    return word


def _convert_name_with_help(name, help_text, separator='(%s)'):
    if not help_text:
        return name
    name_with_help = name + separator % help_text
    return name_with_help

__all__ = [Fregger.__name__, Fregger.generate_doc.__name__]
