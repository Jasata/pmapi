#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware component
# Flask routes
#
# routes.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#   0.2.0   2018.10.20  Route for hit counter data.
#   0.3.0   2018.10.26  Rewritten to match new design.
#
#
#   IMPORTANT!
#
#       REST API implmentation strategy is requires that the route handler
#       encloses whatever code it needs to run, into a 'try ... except'.
#       If non-recoverable error occures, the route handler is required to
#       use the local function 'exception_json()' to produce an error
#       message for the client.
#
#       PATE Monitor JSON API specification states that all API calls return
#       either excepted JSON structure:
#       {"info" : {"version" : <int>, ...}, "data" : [{}, ...]}
#       or exception JSON structure:
#       {"error" : {"type" : <str>, "trace" : <str>}}.
#
#       Client is required to check if the received JSON has key 'error' before
#       assuming that the received data is correct.
#
#   REST actions (std scheme)
#
#       GET     Retrieve all/filtered resources
#       HEAD    Retrieve headers of all/filtered resources
#       POST    Create a new resource
#       PUT     Update a resource
#       DELETE  Delete a resource
#       OPTIONS Return available HTTP methods and other options
#
#   NOTE: POST is NOT idempotent!
#
#       GET {id}            Retrieve specified resource
#       GET [{filter},...]  Retrieve matching resources
#       GET                 Retrieve all resources
#       HEAD                (same as GET)
#       POST                Create resource
#       PUT                 Update resource {id} in body
#       DELETE {id, ...}    Delete identified resource(s)
#       OPTIONS             List supported request actions
#
import sys
import time
import json
import flask
import logging

from flask          import request
from flask          import Response
from flask          import send_from_directory
from flask          import g
# Our Flask application instance
from application    import app

# ApiException classes, data classes
import api

#
# Debug log HTTP request and the rule that serves it
# (application.log)
#
def log_request(request):
    app.logger.debug(
        "{} '{}' (rule: '{}')"
        .format(
            request.method,
            request.path,
            request.url_rule.rule
        )
    )




###############################################################################
#
# PATE Monitor REST JSON API
#
# NOTE: Getting current route
#   request.endpoint        yields handler function name
#   http://flask.pocoo.org/docs/1.0/api/#flask.Request.endpoint
#   request.path            yields path portion of URL
#   http://flask.pocoo.org/docs/1.0/api/#flask.Request.path
#   request.url_rule        same as request.path
#   http://flask.pocoo.org/docs/1.0/api/#flask.Request.url_rule
#
#   HTTP Methods
#       GET     get/query
#       POST    create new
#       PUT     replace existing
#       PATCH   update existing
#       DELETE  delete
#
#   IMPORTANT NOTE ABOUT GET METHODS
#       GET requests shall be divided into TWO (2) separate types; searches and fetches.
#       Search provides zero to N search criteria and yields in zero to N results.
#       Fetch provides a key (ID or elements that make up the primary key) and
#       can only return the specified (one) item or "404 Not Found".
#
#   HTTP Return codes
#       verb    response                payload
#       GET     "200 OK"                'data': [] | {}     List or object, depending on fetch or search
#       GET     "404 Not Found"         'error':<str>       Fetch specified non-existent PK/ID
#       POST    "201 Created"           'id':<int>          INSERT successful, return new ID
#       POST    "404 Not Found"         'error':<str>       Entity ID not found (wrong PK)
#       POST    "405 Method Not Allowed"'error':<str>       POST is unsupported
#       POST    "406 Not Acceptable"    'error':<str>       Problems with provided values (data quality/type issues)
#       POST    "409 Conflict"          'error':<str>       Unique/PK violation, Foreign key not found (structural issues)
#       PUT
#       PATCH   "200 OK"                (entire object)     UPDATE was successful, SELECT new data
#       PATCH   "404 Not Found"         'error':<str>       Entity ID not found (wrong PK)
#       PATCH   "405 Method Not Allowed"'error':<str>       PATCH is unsupported
#       PATCH   "406 Not Acceptable"    'error':<str>       Problems with provided values
#       PATCH   "409 Conflict"          'error':<str>       Unique/PK violation, Foreign key not found (structural issues)
#       DELETE  "200 OK"                None                Delete was successfull
#       DELETE  "404 Not Found"         'error':<str>       Identified item not found
#       DELETE  "405 Method Not Allowed"'error':<str>       DELETE is unsupported
#       DELETE  "409 Conflict"          'error':<str>       Unique/PK violation, Foreign key not found
#
#   NOTE:   "401 Unauthorized" needs to be added when PATE Monitor becomes an EGSE solution.
#           This needs to work WITH the @requires_roles('admin', 'user') or @login_required
#           or whatever is the chosen approach...
#           https://flask-user.readthedocs.io/en/v0.6/authorization.html
#
#   URI's (planned)
#
#       For most (except session management) like;
#       /api/<session>/hitcout?timestamp=152139123
#

#
# Sample Pulse Height Data (to be calibration data?)
#
@app.route('/api/pulseheight', methods=['GET', 'POST'])
def pulseheight():
    log_request(request)
    try:
        # TODO: Remove this request.method test, disallow POST
        if request.method == 'GET':
            from api.PulseHeight import PulseHeight
            return api.response(PulseHeight.get(request))
        else:
            raise api.MethodNotAllowed(
                "Method {} is not supported for '{}'"
                .format(request.method, request.url_rule)
            )
    except api.ApiException as e:
        return api.response(e)
    except Exception as e:
        return api.response(e)


#
# Science Data (hit counters)
#
@app.route('/api/hitcounters', methods=['GET'])
def hitcounters():
    log_request(request)
    try:
        from api.HitCounters import HitCounters
        return api.response(HitCounters.get(request))
    except Exception as e:
        return api.response(e)


#
# Operator notes
#
@app.route('/api/note', methods=['GET', 'POST'])
def note():
    log_request(request)
    try:
        from api.Note import Note
        if request.method == 'POST':
            return api.response(Note.post(request))
        elif request.method == 'GET':
            return api.response(Note.get(request))
        else:
            # Should be impossible
            raise api.MethodNotAllowed(
                "'{}' method not allowed for '{}'"
                .format(request.method, request.url_rule)
            )
    except Exception as e:
        return api.response(e)

#
# Command interface
#
@app.route('/api/psu', methods=['GET', 'POST'])
def psu():
    """Agilent power supply remote control.
    
    GET method will return a row from 'psu' table, containing values:
    'power' ['ON', 'OFF'], indicating if the powerline is fed.
    'voltage' (float), the configured output voltage.
    'current_limit' (float), the configured current limit.
    'measured_current' (float), reported current at output terminal.
    'measured_voltage' (float), reported voltage at output terminal.
    'state' ['OK', 'OVER CURRENT'], reported state of operations.
    'modified' (float), Unix timestamp (with fractions of seconds) on when this row was generated.

    POST method allows setting three PSU parameters:
    'function': 'set voltage', 'value': (float)
    'function': 'set current limit', 'value': (float)
    'function': 'set power', 'value': 'ON' | 'OFF'
    """
    log_request(request)
    try:
        from api.PSU import PSU
        if request.method == 'GET':
            api.response(PSU.get(request))
        elif request.method == 'POST':
            api.response(PSU.post(request))
        else:
            raise api.MethodNotAllowed(
                "Method '{}' not supported for '{}'"
                .format(request.method, request.url_rule)
            )
    except Exception as e:
        return api.response(e)

###############################################################################
#
# System / development URIs
#
#       These routes are to be grouped under '/sys' path, with the notable
#       exception of '/api.html', because that serves the API listing as HTML
#       and because the API documentation is very central to this particular
#       solution.
#
#

#
# Flask Application Configuration
#
@app.route('/sys/cfg', methods=['GET'])
def show_flask_config():
    log_request(request)
    try:
        cfg = {}
        for key in app.config:
            cfg[key] = app.config[key]
        # Censor sensitive values
        for key in cfg:
            if key in ('SECRET_KEY', 'MYSQL_DATABASE_PASSWORD'):
                cfg[key] = '<CENSORED>'
    except Exception as e:
        app.logger.exception(str(e))
    return api.response(cfg)


#
# API listing
#
#       Serves two routes: '/sys/api' and 'api.html'. First returns the listing
#       in JSON format and the second serves a HTML table of the same data.
#
#   NOTES:
#           - Built-in route '/static' is ignored.
#           - Implicit methods 'HEAD' and 'OPTIONS' are hidden.
#             That's not the correct way about doing this, but since this implementation
#             does not use either of them, we can skip this issue and just hide them.
#
#   See also:
#   https://stackoverflow.com/questions/13317536/get-a-list-of-all-routes-defined-in-the-app
#
@app.route('/api.html', methods=['GET'])
@app.route('/sys/api', methods=['GET'])
def api_doc():
    """Generate API document on available endpoints and return it either as JSON or as a HTML/TABLE.
    This functionality replies on PEP 257 (https://www.python.org/dev/peps/pep-0257/)
    convention for docstrings and Flask micro framework route ('rule') mapping
    to generate basic information listing on all the available REST API functions.
    This call has no arguments."""
    def htmldoc(docstring):
        """Some HTML formatting for docstrings."""
        result = None
        if docstring:
            result = "<br/>".join(docstring.split('\n')) + "<br/>"
        return result
    try:
        log_request(request)
        eplist = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                options = {arg : "[{}]".format(arg) for arg in rule.arguments}
                # This options stuff doesn't work... TODO
                url = flask.url_for(rule.endpoint, **options)
                # Strip 'HEAD' and 'OPTIONS', since they are implicit and we do not "serve" them
                allowed = [method for method in rule.methods if method not in ('HEAD', 'OPTIONS')]
                methods = ','.join(allowed)

                eplist.append({
                    'service'   : rule.endpoint,
                    'methods'   : methods,
                    'endpoint'  : url,
                    'doc'       : app.view_functions[rule.endpoint].__doc__
                })

        if 'api.html' in request.url_rule.rule:
            html = "<!DOCTYPE html><html><head><title>API Listing</title>"
            html +="<link rel='stylesheet' href='/css/api.css'></head><body>"
            html += "<table><tr><th>Service</th><th>Methods</th><th>Endpoint</th><th>Documentation</th></tr>"
            for row in eplist:
                html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>" \
                        .format(
                            row['service'],
                            row['methods'],
                            row['endpoint'],
                            htmldoc(row['doc'])
                        )
            html += "</table></body></html>"
            # Create Request object
            response = app.response_class(
                response    = html,
                status      = 200,
                mimetype    = 'text/html'
            )
            return response
        else:
            return api.response({'endpoints': eplist})
    except Exception as e:
        api.response(e)

#
# TODO: Automatic API documentation parsing has issues with options (<int:option>).
#       Needs to be fixed, at some point...
#
#@app.route('/post/<int:post_id>')
#def show_post(post_id):
#    pass

###############################################################################
#
# Static content
#
#   NOTE:   Nginx can be configured (see /etc/nginx/nginx.conf) to serve
#           files of certain suffixes (images, css, js) which are deemed to
#           be always static.
#
#   2018-10-25 JTa:
#           Nginx file suffix configuration would be a never ending chase after
#           new files suffixes. It's not worth it in this application -
#           performance is not a vital concern.
#
#   This is an alternative (albeit little less efficient) approach:
#
#           Certain routes are setup to contain only static files and
#           'send_from_directory()' is used to simply hand out the content.
#           The function is designed to solve a security problems where
#           an attacker would try to use this to dig up .py files.
#           It will raise an error if the path leads to outside of a
#           particular directory.
#
# @app.route('/js/<path:path>')
# def send_js(path):
#     return send_from_directory('js', path)

# @app.route('/css/<path:path>')
# def send_css(path):
#     return send_from_directory('css', path)

# @app.route('/img/<path:path>')
# def send_img(path):
#     return send_from_directory('img', path)

#
# Catch-all for other paths (UI HTML files)
#
@app.route('/<path:path>', methods=['GET'])
# No-path case
@app.route('/', methods=['GET'])
def send_ui(path = 'index.html'):
    log_request(request)
    return send_from_directory('ui', path)



# EOF
