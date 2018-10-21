#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# uWSGI entry point
#
# wsgi.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#   0.1.1   2018.10.14  Fixed the version output in the logging message.
#
#
#   uWSGI configuration (uwsgi.ini) specifies flask app directory to be
#   ("chdir = /srv/nginx-root/") and that the 'application' is to be found
#   in this module ("module = application"  =>  'application.py').
#
#   If the execution directory ("chdir" in uwsgi.ini) changes,
#   this file has to be updated accordingly.
#
#   NOTE
#       It appears that Flask has built-in feature to look for
#       (or require) an object specifically named "application".
#
#       Since the application is in directory "pmapi", and since
#       the Flask is created in ./pmapi/__init__.py ("app = Flask()")
#       the import needs to be:
#
from pmapi import app as application


#
# This logging happens only once, when uWSGI daemon starts
#
import logging
logging.basicConfig(
    filename=application.config.get('LOG_FILENAME', 'uwsgi.log'),
    level=logging.DEBUG
)
logging.info(
    "\n"
    "==============================================================\n"
    "PATE Monitor REST API (PMAPI) Flask application started\n"
    "Turku University (2018) Department of Future Technologies\n"
    "Version {}, Jani Tammi <jasata@utu.fi>\n"
    .format(application.config.get('VERSION', '(undefined)'))
)

# THIS WOULD NEVER EXECUTED in normal uWSGI usage (just a FYI)
#if __name__ == "__main__":
#    application.run()


# EOF
