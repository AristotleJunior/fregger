#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
setup(
    name='Fregger',
    version='0.10.7',
    keywords=('flask', 'flask-restful', 'swagger', 'automatically'),
    description='Automatically generate Swagger docs for Flask-Restful.',
    license='MIT',
    author='rain',
    author_email='rain@joymud.com',
    url='https://github.com/AristotleJunior/fregger',
    platforms='any',
    packages=['fregger'],
    package_data={
        'fregger': [
          'static/*.*',
          'static/css/*.*',
          'static/fonts/*.*',
          'static/images/*.*',
          'static/lang/*.*',
          'static/lib/*.*',
        ]
    },
    install_requires=['Flask-Restful'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

