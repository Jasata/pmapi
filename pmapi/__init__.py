#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Flask application initialization
#
# pmapi/__init__.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#
import os
import logging
import sqlite3

from logging.handlers       import RotatingFileHandler
from logging                import Formatter
from flask                  import Flask
from flask                  import g


# For some reason, if Flask() is given 'debug=True',
# uWSGI cannot find the application and startup fails.
#
# The behavior of relative paths in config files can be flipped
# between “relative to the application root” (the default) to 
# “relative to instance folder” via the instance_relative_config
# switch to the application constructor:
app = Flask(
    __name__,
    instance_relative_config=True
)
# ..., instance_path='/path/to/instance/folder') BUT this is constrained

# With Flask 0.8 a new attribute was introduced: Flask.instance_path.
# It refers to a new concept called the “instance folder”. The instance
# folder is designed to not be under version control and be deployment
# specific. It’s the perfect place to drop things that either change at
# runtime or configuration files.
#
# Config file is in ../instance/pmapi.conf
# ('instance_relative_config=True')
app.config.from_pyfile('pmapi.conf')

# Logging
handler = RotatingFileHandler(
    app.config.get('LOG_FILENAME', 'flask.log'),
    maxBytes=10000,
    backupCount=1
)
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    )
)
app.logger.addHandler(handler)
app.logger.debug("=== app.logger setup! ===")


@app.before_request
def before_request():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    app.logger.debug("@app.before_request")
    if not hasattr(g, 'db'):
        g.db = sqlite3.connect(
            app.config.get('SQLITE3_DATABASE_FILE', 'pmapi.sqlite3')
        )
    return

#
# Routes in 'pmapi/routes.py'
#
from pmapi import routes

#
# Executed each time application context tears down
# (request ends)
#
@app.teardown_request
def teardown_request(error):
    """
    Closes the database again at the end of the request.
    """
    app.logger.debug("@app.teardown_request")
    if hasattr(g, 'db'):
        g.db.close()


# EOF
