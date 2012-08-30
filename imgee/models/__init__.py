# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import SQLAlchemy
from imgee import app

db = SQLAlchemy(app)

from imgee.models.user import *
from imgee.models.uploaded_file import *
from imgee.models.thumbnail import *
