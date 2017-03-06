#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/3/5 11:07
# @Author  : Rain
# @Desc    : Automatically generate Swagger docs for Flask-Restful
# @File    : __init__.py.py

from flask import Flask
from flask_restful import Api, Resource, reqparse
# pip install fregger
from fregger import Fregger

app = Flask(__name__)

# Blueprints are also supported 

api = Api(app, prefix='/api/v1')
fregger = Fregger(api, title='APIs for admins modules')

parser = reqparse.RequestParser()
parser.add_argument('name', type=str, location='json', store_missing=False)
parser.add_argument('email', type=str, location='json', store_missing=False)
parser.add_argument('password', type=str, location='json', store_missing=False)


class AdminResource(Resource):

    @fregger.generate_doc(summary='Retrieve specific admin info')
    def get(self, aid):
        return {'info': 'info of admin %d' % aid}

    @fregger.generate_doc(parser, summary='Modify specific admin info')
    def post(self, aid):

        # Modify admin info here

        return {'status': 'ok'}


# must setup fregger before add_resource
api.add_resource(AdminResource, '/admins')

if __name__ == "__main__":
    # Fregger is only enabled under DEBUG mode for security reason
    app.config['DEBUG'] = True
    app.run()

# now you can visit http://localhost:5000/api/v1/fregger.html
