# -*- coding: utf-8 -*-

# The imports in this file are order-sensitive

import os
from celery import Celery

from flask import Flask, redirect, url_for
from flask.ext.lastuser import LastUser
from baseframe import baseframe, assets, Version
import coaster.app
from ._version import __version__


version = Version(__version__)
app = Flask(__name__, instance_relative_config=True)
lastuser = LastUser()
celery = Celery()

assets['imgee.css'][version] = 'css/app.css'

import imgee.models
import imgee.views
import imgee.api
from imgee.models import db

registry = imgee.async.TaskRegistry()

def mkdir_p(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def error403(error):
    return redirect(url_for('login'))


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    baseframe.init_app(app, requires=['baseframe', 'picturefill', 'imgee'])
    app.error_handlers[403] =  error403
    app.config.get('NETWORKBAR_LINKS', []).append({
        'name': 'imgee',
        'title': 'Images',
        'url': None,
        })
    lastuser.init_app(app)
    if app.config.get('MEDIA_DOMAIN') and (
            app.config['MEDIA_DOMAIN'].startswith('http:') or
            app.config['MEDIA_DOMAIN'].startswith('https:')):
        app.config['MEDIA_DOMAIN'] = app.config['MEDIA_DOMAIN'].split(':', 1)[1]
    mkdir_p(app.config['UPLOADED_FILES_DEST'])
    celery.conf.add_defaults(app.config)
    registry.set_connection()
