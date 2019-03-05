# pmgui
PATE Monitor UI code (Flask REST API + Web UI)

This application is intended for Foresail-1 PATE development and testing purposes, but the Web UI (and REST API it uses) can be recycled into mission time EGSE purposes, if the platform team so chooses.

## How to Clone with Submodules

     git clone --recurse-submodules https://github.com/jasata/pmapi .

## How to update as submodule

    # change to the submodule directory
    cd ui

    # checkout desired branch
    git checkout master

    # update
    git pull

    # get back to your project root
    cd ..

    # now the submodules are in the state you want, so
    git commit -am "Pulled down update to /ui"

## nginx Configuration
Site file '/etc/nginx/sites-available/default' (or which ever is relevant) needs to reflect uWSGI configuration.

    server {
        listen 80 default_server;
        listen [::]:80 default_server;
    
        root /srv/nginx-root;
        server_name _;
        location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/patemon.uwsgi.sock;
        }
    }

Issue 'systemctl restart nginx' to apply changes

## Instance Configuration
This Flask application holds configuration information in '/srv/nginx-root/instance' directory.
Create this directory and 'application.conf' file into it (0440 www-data.www-data):

    #! /usr/bin/env python3
    # -*- coding: utf-8 -*-
    #
    # Turku University (2018) Department of Future Technologies
    # Foresail-1 / PATE Monitor / Middleware (PMAPI)
    # Flask application configuration
    #
    # application.conf - Jani Tammi <jasata@utu.fi>
    #
    #   0.1.0   2018.10.11  Initial version.
    #   0.2.0   2018.10.23  Renamed as 'application.conf'
    #   0.3.0   2018.10.23  Move version numbers to APIVERSION and APPVERSION.
    #
    #
    # See http://flask.pocoo.org/docs/0.12/config/ for built-in config values.
    #
    # To generate SECRET_KEY:
    # >>> import os
    # >>> os.urandom(24)
    # b'\xb5R\x8d\x8aZa\x07\x90i\xe5Y\xff\x9e|\xe8p\x0b\x86;\xc3}\xd0\xfc?'
    #
    import os
    import logging

    DEBUG                    = True
    SESSION_COOKIE_NAME      = 'pmapisession'
    SECRET_KEY               = b'\xb5R...'
    EXPLAIN_TEMPLATE_LOADING = True
    TOP_LEVEL_DIR            = os.path.abspath(os.curdir)
    BASEDIR                  = os.path.abspath(os.path.dirname(__file__))


    #
    # Command table configuration (seconds)
    #
    COMMAND_TIMEOUT         = 0.5
    COMMAND_POLL_INTERVAL   = 0.2


    #
    # Flask app logging
    #
    LOG_FILENAME             = 'application.log'
    LOG_LEVEL                = 'DEBUG'              # DEBUG, INFO, WARNING, ERROR, CRITICAL


    #
    # MariaDB configuration
    #
    MYSQL_DATABASE_HOST      = 'localhost'
    MYSQL_DATABASE_PORT      = 3306
    MYSQL_DATABASE_USER      = 'dummy'
    MYSQL_DATABASE_PASSWORD  = 'dummy'
    MYSQL_DATABASE_DB        = 'pmapi'
    MYSQL_DATABASE_CHARSET   = 'utf8'	# PyMySQL requires 'utf8', most others want 'utf-8'

    #
    # SQLite3 configuration
    #
    SQLITE3_DATABASE_FILE   = 'pmapi.sqlite3'

    #
    # Flask email
    #



    # EOF


Generate your personal SECRET_KEY and change database credentials to match your actual credentials.
