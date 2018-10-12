#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware component
# Flask application
#
# uwsgi.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#
#
#   uWSGI configuration (uwsgi.ini) specifies flask app directory
#   to be "chdir = /srv/nginx-root". Flask application is located in
#   "/srv/nginx-root/application".
#
#   If the execution directory ("chdir" in uwsgi.ini) changes,
#   this file has to be updated accordingly.
#
#   NOTE
#       It appears that Flask has built-in feature to look for
#       (or require) an object specifically named "application".
#
#       If your application would be in a directory "pmapi", for
#       example, and if ./pmapi/__init__py creates the object as
#       myapp = Flask(...), then your import would need to be:
#
#       from pmapi import myapp as application
#
#

# The below import 'matches' ./application/__init__.py
# which instantiates app = Flask(...)
# From ./application/__init__.py, object 'app'
from application import app as application


#
# This logging happens only once, when uWSGI daemon starts
#
import logging
logging.basicConfig(
    filename=application.config.get('LOG_FILENAME', 'flask.log'),
    level=logging.DEBUG
)
logging.info(
    "\n"
    "==============================================================\n"
    "PATE Monitor Middleware (PMAPI) Flask application started\n"
    "Turku University (2018) Jani Tammi <jasata@utu.fi>\n"
    "Version {}".formatapplication.config.get('VERSION', '(unknown)'))
)

# EOF
