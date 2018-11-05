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
#   0.3.1   2018.10.28  Added docstrings.
#   0.3.2   2018.10.31  Fixed automatic endpoint listing.
#   0.3.3   2018.10.31  HTML brackets converted for HTML output only.
#   0.3.4   2018.11.05  Comments and docstrings.
#
#
#   Actual processing is to be done API resource classes/objects. HTTP response
#   should be created by API services (written in 'api/__init__.py'). Route
#   handlers need to enclose all their code into a try ... except block and
#   in the event of an exception, return with api.exception_response().
#   Normal return should be done with:
#
#       api.response()              Normal JSON replies
#       api.exception_response()    Any exception into JSON error reply
#       api.stream_result_as_csv()  Stream SQLite3.Cursor out as CSV
#
#
#   PATTERN FOR ROUTES
#
#       @app.route('/api/endpoint', methods=['GET', 'POST'])
#       def service():
#           """This docstring will appear in automatic documentation!"""
#           log_request(request)
#           try:
#               from api import ResourceObject
#               if request.method == 'GET':
#                   api.response(ResourceObject(request).get())
#               elif request.method == 'POST':
#                   api.response(ResourceObject(request).post())
#               else:
#                   raise api.MethodNotAllowed(
#                       "Method '{}' not supported for '{}'"
#                       .format(request.method, request.url_rule)
#                   )
#           except Exception as e:
#               return api.exception_response(e)
#
#   (Modify docstring, endpoint and the ResourceObject (at least).)
#
#
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
#   NOTE:   "401 Unauthorized" needs to be added when PATE Monitor becomes an EGSE solution.
#           This needs to work WITH the @requires_roles('admin', 'user') or @login_required
#           or whatever is the chosen approach...
#           https://flask-user.readthedocs.io/en/v0.6/authorization.html
#
#


###############################################################################
#
# REST API ENDPOINTS (routes)
#
###############################################################################


#
# Sample Pulse Height Data (to be calibration data?)
#
@app.route('/api/pulseheight', methods=['GET'])
def pulseheight():
    """Raw PATE pulse height data."""
    log_request(request)
    try:
        from api.PulseHeight import PulseHeight
        return api.response(PulseHeight(request).get())
    except Exception as e:
        # Handles both ApiException and Exception derivates
        return api.exception_response(e)



#
# Science Data (hit counters)
#
@app.route('/api/classifieddata', methods=['GET'])
@app.route('/api/classifieddata/<string:function>', methods=['GET'])
def classifieddata(function=None):
    """PATE Classified particle hits.

    Data is logically grouped into full rotations, each identified by the
    timestamp when the rotation started. Information on rotational period
    or starting time of each sector is not available within data. It must
    be deciphered separately, if needed.
    
    Request parameters:
    begin - PATE timestamp
    end - PATE timestamp
    fields - A comma separated list of fields to return
    
    Parameters 'begin' and 'end' are datetime data in timestamp format (TBS) and
    are compared against the primary key value 'rotation'.
    While the timestamp format remains without specification,
    Python timestamps (UNIX timestamps with fractions) should be used.
    
    GET /api/classifieddata

    A JSON list of objects is returned. Among object properties, primary key
    'rotation' is always included, regardless what 'fields' argument specifies.
    Data exceeding 7 days should not be requested. For more data, CSV services
    should be used.

    GET /api/classifieddata/<string:function>

    Unlike in the above described API endpoint, these responses do not
    explicitly include primary key field ('rotation'), because that would
    defeat the purpose of the aggregate functions. Allowed aggregate functions
    are: avg, sum, min, max, count.
    """
    log_request(request)
    try:
        from api.ClassifiedData import ClassifiedData
        if str(request.url_rule) == '/api/classifieddata':
            return api.response(ClassifiedData(request).get())
        if str(request.url_rule) == '/api/classifieddata/<string:function>':
            if function.lower() not in ('avg', 'sum', 'min', 'max', 'count'):
                raise api.InvalidArgument(
                    "Function '{}' is not supported!".format(function)
                )
            return api.response(ClassifiedData(request).get(function))
    except Exception as e:
        # Handles both ApiException and Exception derivates
        return api.exception_response(e)





#
# Housekeeping
#
@app.route('/api/housekeeping', methods=['GET'])
@app.route('/api/housekeeping/<string:function>', methods=['GET'])
def housekeeping(function=None):
    """PATE Housekeeping data.

    Data is currently not specified.
    
    Request parameters:
    begin - PATE timestamp
    end - PATE timestamp
    fields - A comma separated list of fields to return
    
    Parameters 'begin' and 'end' are datetime data in timestamp format (TBS) and
    are compared against the primary key value 'timestamp'.
    While the timestamp format remains without specification,
    Python timestamps (UNIX timestamps with fractions) should be used.
    
    GET /api/housekeeping

    A JSON list of objects is returned. Among object properties, primary key
    'timestamp' is always included, regardless what 'fields' argument specifies.
    Data exceeding 7 days should not be requested. For more data, CSV services
    should be used.

    GET /api/housekeeping/<string:function>

    Unlike in the above described API endpoint, these responses do not
    explicitly include primary key field ('timestamp'), because that would
    defeat the purpose of the aggregate functions. Allowed aggregate functions
    are: avg, sum, min, max, count.
    """
    log_request(request)
    try:
        from api.Housekeeping import Housekeeping
        if str(request.url_rule) == '/api/housekeeping':
            return api.response(Housekeeping(request).get())
        if str(request.url_rule) == '/api/housekeeping/<string:function>':
            if function.lower() not in ('avg', 'sum', 'min', 'max', 'count'):
                raise api.InvalidArgument(
                    "Function '{}' is not supported!".format(function)
                )
            return api.response(Housekeeping(request).get(function))
    except Exception as e:
        return api.exception_response(e)



#
# Register
#
@app.route('/api/register/<int:register_id>', methods=['GET', 'POST'])
def register(register_id):
    """Not yet implemented"""
    log_request(request)
    try:
        raise api.NotImplemented()
    except Exception as e:
        return api.exception_response(e)



#
# Operator notes
#
@app.route('/api/note', methods=['GET', 'POST'])
def note():
    """Not yet implemented!"""
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
        # Handles both ApiException and Exception derivates
        return api.exception_response(e)

#
# Command interface
#
@app.route('/api/psu', methods=['GET'])
@app.route('/api/psu/voltage', methods=['GET', 'POST'])
@app.route('/api/psu/current', methods=['GET'])
@app.route('/api/psu/current/limit', methods=['GET', 'POST'])
@app.route('/api/psu/power', methods=['GET', 'POST'])
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
    'function': 'SET_VOLTAGE', 'value': (float)
    'function': 'SET_CURRENT_LIMIT', 'value': (float)
    'function': 'SET_POWER', 'value': 'ON' | 'OFF'
    """
    log_request(request)
    try:
        from api.PSU import PSU
        if str(request.url_rule) == '/api/psu' and request.method == 'GET':
            api.response(PSU.get(request))
        elif str(request.url_rule) == '/api/psu/voltage' and request.method == 'POST':
            api.response(PSU.post(request))
        elif str(request.url_rule) == '/api/psu/current' and request.method == 'POST':
            api.response(PSU.post(request))
        else:
            raise api.MethodNotAllowed(
                "Method '{}' not supported for '{}'"
                .format(request.method, request.url_rule)
            )
    except Exception as e:
        # Handles both ApiException and Exception derivates
        return api.exception_response(e)




###############################################################################
#
# CSV exports
#
#
@app.route('/csv/classifieddata', methods=['GET'])
def csv_classifieddata():
    """Export PATE hit counts into CSV file.

    Request parameters:
    begin - PATE timestamp
    end - PATE timestamp
    fields - A comma separated list of fields to return

    All request parameters are optional. 'being' and 'end' timestamps limit the
    result set and 'fields' limits the columns to the listed (and primary key,
    which is always included).
    """
    log_request(request)
    try:
        from api.ClassifiedData import ClassifiedData
        # Use .query() method which returns sqlite3.Cursor object
        return api.stream_result_as_csv(ClassifiedData(request).query())
    except Exception as e:
        app.logger.exception(
            "CSV generation failure! " + str(e)
        )
        raise


@app.route('/csv/pulseheight', methods=['GET'])
def csv_pulseheight():
    """Export PATE raw pulse height data into CSV file.
    NOT YET IMPLEMENTED!"""
    log_request(request)
    return app.response_class(status = 501, mimetype = "text/html")


@app.route('/csv/housekeeping', methods=['GET'])
def csv_housekeeping():
    """Export PATE housekeeping data into CSV file.

    Request parameters:
    begin - PATE timestamp
    end - PATE timestamp
    fields - A comma separated list of fields to return

    All request parameters are optional. 'being' and 'end' timestamps limit the
    result set and 'fields' limits the columns to the listed (and primary key,
    which is always included).
    """
    log_request(request)
    try:
        from api.Housekeeping import Housekeeping
        return api.stream_result_as_csv(Housekeeping(request).query())
    except Exception as e:
        app.logger.exception(
            "CSV generation failure! " + str(e)
        )
        raise
    #return app.response_class(status = 501, mimetype = "text/html")


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
    """Middleware (Flask application) configuration. Sensitive entries are
    censored."""
    log_request(request)
    try:
        cfg = {}
        for key in app.config:
            cfg[key] = app.config[key]
        # Censor sensitive values
        for key in cfg:
            if key in ('SECRET_KEY', 'MYSQL_DATABASE_PASSWORD'):
                cfg[key] = '<CENSORED>'
        return api.response((200, cfg))
    except Exception as e:
        return api.exception_response(e)


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
    """JSON API Documentation.

    Generates API document from the available endpoints. This functionality
    replies on PEP 257 (https://www.python.org/dev/peps/pep-0257/) convention
    for docstrings and Flask micro framework route ('rule') mapping to
    generate basic information listing on all the available REST API functions.

    This call takes no arguments.
    
    GET /sys/api
    
    List of API endpoints is returned in JSON.
    
    GET /api.html
    
    The README.md from /api is prefixed to HTML content. List of API endpoints
    is included as a table."""
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
                allowed = [method for method in rule.methods if method not in ('HEAD', 'OPTIONS')]
                methods = ','.join(allowed)

                eplist.append({
                    'service'   : rule.endpoint,
                    'methods'   : methods,
                    'endpoint'  : str(rule),
                    'doc'       : app.view_functions[rule.endpoint].__doc__
                })


        #
        # Sort eplist based on 'endpoint'
        #
        eplist = sorted(eplist, key=lambda k: k['endpoint'])


        if 'api.html' in request.url_rule.rule:
            try:
                from ext.markdown2 import markdown
                with open('api/README.md') as f:
                    readme = markdown(f.read())
            except:
                app.logger.exception("Unable to process 'api/README.md'")
                readme = ''
            html =  "<!DOCTYPE html><html><head><title>API Listing</title>"
            html += "<link rel='stylesheet' href='/css/api.css'></head><body>"
            html += readme
            html += "<table><tr><th>Service</th><th>Methods</th><th>Endpoint</th><th>Documentation</th></tr>"
            for row in eplist:
                html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>" \
                        .format(
                            row['service'],
                            row['methods'],
                            row['endpoint'].replace('<', '&lt;').replace('>', '&gt;'),
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
            return api.response((200, {'endpoints': eplist}))
    except Exception as e:
        return api.exception_response(e)

#
# Catch-all for non-existent API requests
#
@app.route('/api', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
@app.route('/api/', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def api_not_implemented(path = ''):
    """Catch-all route for '/api*' access attempts that do not match any defined routes.
    "405 Method Not Allowed" JSON reply is returned."""
    log_request(request)
    try:
        raise api.MethodNotAllowed(
            "Requested API endpoint ('{}') does not exist!"
            .format("/api/" + path)
        )
    except Exception as e:
        return api.exception_response(e)


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
# NOTE: Development time request from Rameez;
#       Allow directory listings under ui/
#       Configured into /etc/nginx/sites-available/default
#       You should not have index.html in '/ui', or listing will not show.
#


#
# Catch-all for other paths (UI HTML files)
#
@app.route('/<path:path>', methods=['GET'])
# No-path case
@app.route('/', methods=['GET'])
def send_ui(path = 'dev_index.html'):
    """Send static HTML/CSS/JS/images/... content."""
    log_request(request)
    return send_from_directory('ui', path)



# EOF
