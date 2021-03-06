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
#   0.3.5   2018.11.11  ClassifiedData renamed to Hitcount
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
# Debug log-function
#       Store HTTP request path and the rule that triggered.
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
#       GET requests shall be divided into TWO (2) separate types;
#       searches and fetches. Search provides zero to N search criteria
#       and yields in zero to N results. Fetch provides a key (ID or
#       elements that make up the primary key) and can only return the
#       specified (one) item or "404 Not Found".
#
#   NOTE:   "401 Unauthorized" needs to be added when PATE Monitor
#           becomes an EGSE solution. This needs to work WITH the
#           @requires_roles('admin', 'user') or @login_required
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
# Raw Pulse Height Data
#
@app.route('/api/pulseheight', methods=['GET'])
def pulseheight():
    """Raw PATE pulse height data.
    
    GET /api/pulseheight
    Query parameters:
    begin - PATE timestamp (Unix timestamp)
    end - PATE timestamp (Unix timestamp)
    fields - A comma separated list of fields to return
    API returns 200 OK and:
    {
        ...,
        "data" : [
            {
                <fields according to query parameter 'fields'>
            },
            ...
        ],
        ...
    }
    """
    log_request(request)
    try:
        from api.PulseHeight import PulseHeight
        return api.response(PulseHeight(request).get())
    except Exception as e:
        return api.exception_response(e)



@app.route('/api/pulseheight/<string:function>', methods=['GET'])
def pulseheight_aggregate(function):
    """Aggregated raw PATE pulse height data.

    GET /api/pulseheight/<string:function>
    Allowed aggregate functions are: avg, sum, min, max and count.
    Query parameters:
    begin - PATE timestamp (Unix timestamp)
    end - PATE timestamp (Unix timestamp)
    fields - A comma separated list of fields to return
    API returns 200 OK and:
    {
        ...,
        "data" : [
            {
                <fields according to query parameter 'fields'>
            },
            ...
        ],
        ...
    }
    """
    log_request(request)
    try:
        from api.PulseHeight import PulseHeight
        if function.lower() not in ('avg', 'sum', 'min', 'max', 'count'):
            raise api.InvalidArgument(
                "Function '{}' is not supported!".format(function)
            )
        return api.response(PulseHeight(request).get(function))
    except Exception as e:
        return api.exception_response(e)



#
# Science Data (hit counters)
#
@app.route('/api/hitcount', methods=['GET'])
def hitcount():
    """Classified PATE hit counters

    GET /api/hitcount
    Query parameters:
    begin - PATE timestamp (Unix timestamp)
    end - PATE timestamp (Unix timestamp)
    fields - A comma separated list of fields to return
    API returns 200 OK and:
    {
        ...,
        "data" : [
            {
                <fields according to query parameter 'fields'>
            },
            ...
        ],
        ...
    }


    Data is logically grouped into full rotations, each identified by the timestamp when the rotation started. Field/column descriptions are unavailable until they have been formally specified by instrument development.

    Parameters 'begin' and 'end' are integers, although the 'rotation' field they are compared to, is a decimal number. NOTE: This datetime format is placeholder, because instrument development has not formally specified the one used in the actual satellite. Internally, Python timestamp is used.

    A JSON list of objects is returned. Among object properties, primary key 'timestamp' is always included, regardless what 'fields' argument specifies. Data exceeding 7 days should not be requested. For more data, CSV services should be used."""
    log_request(request)
    try:
        from api.HitCount import HitCount
        return api.response(HitCount(request).get())
    except Exception as e:
        return api.exception_response(e)



@app.route('/api/hitcount/<string:function>', methods=['GET'])
def hitcount_aggregate(function):
    """Aggregated classified PATE particle hits

    GET /api/hitcount/<string:function>
    Allowed aggregate functions are: avg, sum, min, max and count.
    Query parameters:
    begin - PATE timestamp (Unix timestamp)
    end - PATE timestamp (Unix timestamp)
    fields - A comma separated list of fields to return
    API returns 200 OK and:
    {
        ...,
        "data" : {
            <fields according to query parameter 'fields'>
        },
        ...
    }

    Data is logically grouped into full rotations, each identified by the timestamp when the rotation started. Information on rotational period or starting time of each sector is not available within data. It must be deciphered separately, if needed.

    Parameters 'begin' and 'end' are integers, although the 'rotation' field they are compared to, is a decimal number. NOTE: This datetime format is placeholder, because instrument development has not formally specified the one used in the actual satellite. Internally, Python timestamp is used.

    A JSON list containing a single object is returned. The identifier field ('timestamp') is never included, because that would defeat the purpose of the aggregate functions."""
    log_request(request)
    try:
        from api.HitCount import HitCount
        if function.lower() not in ('avg', 'sum', 'min', 'max', 'count'):
            raise api.InvalidArgument(
                "Function '{}' is not supported!".format(function)
            )
        return api.response(HitCount(request).get(function))
    except Exception as e:
        return api.exception_response(e)




#
# Housekeeping
#
@app.route('/api/housekeeping', methods=['GET'])
def housekeeping():
    """PATE Housekeeping data

    GET /api/housekeeping
    Query parameters:
    begin - PATE timestamp (Unix timestamp)
    end - PATE timestamp (Unix timestamp)
    fields - A comma separated list of fields to return
    API returns 200 OK and:
    {
        ...,
        "data" : [
            {
                <fields according to query parameter 'fields'>
            },
            ...
        ],
        ...
    }

    Parameters 'begin' and 'end' are integers, although the 'rotation' field they are compared to, is a decimal number. NOTE: This datetime format is placeholder, because instrument development has not formally specified the one used in the actual satellite. Internally, Python timestamp is used.

    A JSON list of objects is returned. Among object properties, primary key 'timestamp' is always included, regardless what 'fields' argument specifies. Data exceeding 7 days should not be requested. For more data, CSV services should be used."""
    log_request(request)
    try:
        from api.Housekeeping import Housekeeping
        return api.response(Housekeeping(request).get())
    except Exception as e:
        return api.exception_response(e)



@app.route('/api/housekeeping/<string:function>', methods=['GET'])
def housekeeping_aggregate(function):
    """Aggregated PATE Housekeeping data

    GET /api/housekeeping/<string:function>
    Allowed aggregate functions are: avg, sum, min, max and count.
    Query parameters:
    begin - PATE timestamp (Unix timestamp)
    end - PATE timestamp (Unix timestamp)
    fields - A comma separated list of fields to return
    API returns 200 OK and:
    {
        ...,
        "data" : {
            <fields according to query parameter 'fields'>
        },
        ...
    }

    Parameters 'begin' and 'end' are integers, although the 'timestamp' field they are compared to, is a decimal number. NOTE: This datetime format is placeholder, because instrument development has not formally specified the one used in the actual satellite. Internally, Python timestamp is used.

    Unlike in the above described API endpoint, these responses do not explicitly include primary key field ('timestamp'), because that would defeat the purpose of the aggregate functions.
    """
    log_request(request)
    try:
        from api.Housekeeping import Housekeeping
        if function.lower() not in ('avg', 'sum', 'min', 'max', 'count'):
            raise api.InvalidArgument(
                "Function '{}' is not supported!".format(function)
            )
        return api.response(Housekeeping(request).get(function))
    except Exception as e:
        return api.exception_response(e)




#
# PSU
#
@app.route('/api/psu', methods=['GET'])
def psu():
    """Read PSU values.

    GET /api/psu
    No query parameters supported.
    API returns 200 OK and:
    {
        ...,
        "data" : {
            "power"             : ("OFF" | "ON"),
            "state"             : ("OK" | "OVER CURRENT"),
            "measured_current"  : (float),
            "measured_voltage"  : (float),
            "voltage_setting"   : (float),
            "current_limit"     : (float),
            "modified"          : (int)
        },
        ...
    }

    If the backend is not running, 404 Not Found is returned.
    """
    log_request(request)
    try:
        from api.PSU import PSU
        return api.response(PSU(request).get())
    except Exception as e:
        return api.exception_response(e)


@app.route('/api/psu/voltage', methods=['GET', 'POST'])
def psu_voltage():
    """Read or set PSU output voltage.

    GET /api/psu/voltage
    No query parameters supported.
    Response returns:
    {
        ...,
        "data" : {
            "measured_voltage"  : (float),
            "voltage_setting"   : (float),
            "modified"          : (int)
        },
        ...
    }

    POST /api/psu/voltage
    Required payload:
    {
        "voltage" : (float)
    }
    API will respond with 202 Accepted and:
    {
        ...,
        "data" : {
            "command_id" : (int)
        },
        ...
    }
    """
    log_request(request)
    try:
        include = [
            'measured_voltage',
            'voltage_setting',
            'modified'
        ]
        if request.method == 'GET':
            from api.PSU import PSU
            return api.response(PSU(request).get(include))
        else:
            from api.Command import Command
            return api.response(Command(request).post("PSU", "SET VOLTAGE"))
    except Exception as e:
        return api.exception_response(e)


@app.route('/api/psu/current', methods=['GET'])
def psu_current():
    """Read PSU current.

    GET /api/psu/voltage
    No query parameters supported.
    Response returns:
    {
        ...,
        "data" : {
            "measured_current"  : (float),
            "current_limit"     : (float),
            "modified"          : (int)
        },
        ...
    }"""
    log_request(request)
    try:
        include = [
            'measured_current',
            'current_limit',
            'modified'
        ]
        from api.PSU import PSU
        return api.response(PSU(request).get(include))
    except Exception as e:
        return api.exception_response(e)


@app.route('/api/psu/current/limit', methods=['GET', 'POST'])
def psu_current_limit():
    """Read or Set Current Limit Value from PSU.

    GET /api/psu/current/limit
    No query parameters supported.
    Response returns:
    {
        ...,
        "data" : {
            "current_limit" : (float),
            "modified"      : (int)
        },
        ...
    }

    POST /api/psu/current/limit
    Required payload:
    {
        "current_limit" : (float)
    }
    API will respond with 202 Accepted and:
    {
        ...,
        "data" : {
            "command_id" : (int)
        },
        ...
    }
    """
    log_request(request)
    try:
        include = [
            'current_limit',
            'modified'
        ]
        if request.method == 'GET':
            from api.PSU import PSU
            return api.response(PSU(request).get(include))
        else:
            from api.Command import Command
            return api.response(Command(request).post("PSU", "SET CURRENT LIMIT"))
    except Exception as e:
        return api.exception_response(e)


@app.route('/api/psu/power', methods=['GET', 'POST'])
def psu_power():
    """Agilent power supply remote control.

    GET /api/psu/power
    No query parameters supported.
    Response returns:
    {
        ...,
        "data" : {
            "power": ["ON", "OFF"],
            "modified": (int)
        },
        ...
    }

    POST /api/psu/power
    No query parameters supported.
    Required payload:
    {
        "power" : ("ON" | "OFF")
    }
    API will respond with 202 Accepted and:
    {
        ...,
        "data" : {
            "command_id" : (int)
        },
        ...
    }
    """

    log_request(request)
    try:
        include = [
            'power',
            'modified'
        ]
        if request.method == 'GET':
            from api.PSU import PSU
            return api.response(PSU(request).get(include))
        else:
            from api.Command import Command
            return api.response(Command(request).post("PSU", "SET POWER"))
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
    """Search or create note(s).

    GET /api/note
    Query parameters:
    begin - PATE timestamp (Unix timestamp)
    end - PATE timestamp (Unix timestamp)
    API responds with 200 OK and:
    {
        ...,
        "data" : [
            {
                "id"            : (int),
                "session_id"    : (int),
                "text"          : (str),
                "created"       : (int)
            },
            ...
        ],
        ...
    }

    POST /api/note
    No query parameters supported.
    Required payload:
    {
        "text" : (str)
    }
    API will respond with 200 OK and:
    {
        ...,
        "data" : {
            id" : (int)
        },
        ...
    }
    """
    log_request(request)
    try:
        from api.Note import Note
        note = Note(request)
        if request.method == 'POST':
            return api.response(note.create())
        elif request.method == 'GET':
            return api.response(note.search())
        else:
            # Should be impossible
            raise api.MethodNotAllowed(
                "'{}' method not allowed for '{}'"
                .format(request.method, request.url_rule)
            )
    except Exception as e:
        return api.exception_response(e)



@app.route('/api/note/<int:timestamp>', methods=["GET"])
def note_by_id(timestamp):
    """Fetch operator note (identified by timestamp).
    
    GET /api/note/<int:timestamp>
    No query parameters supported.
    API responds with 200 OK and:
    {
        ...,
        "data" : {
            "id"            : (int),
            "session_id"    : (int),
            "text"          : (str),
            "created"       : (int)
        },
        ...
    }
    """
    log_request(request)
    try:
        from api.Note import Note
        note = Note(request)
        api.response(note.fetch(timestamp))
    except Exception as e:
        return api.exception_response(e)






###############################################################################
#
# CSV exports
#
#
@app.route('/csv/hitcount', methods=['GET'])
def hitcount_csv():
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
        from api.HitCount import HitCount
        # Use .query() method which returns sqlite3.Cursor object
        return api.stream_result_as_csv(HitCount(request).query())
    except api.ApiException as e:
        app.logger.warning(str(e))
        return flask.Response(str(e), status=e.code, mimetype="text/plain")
    except Exception as e:
        app.logger.exception(
            "CSV generation failure! " + str(e)
        )
        raise



@app.route('/csv/pulseheight', methods=['GET'])
def pulseheight_csv():
    """Export PATE raw pulse height data into CSV file.
    NOT YET IMPLEMENTED!"""
    log_request(request)
    try:
        from api.PulseHeight import PulseHeight
        return api.stream_result_as_csv(PulseHeight(request).query())
    except api.ApiException as e:
        app.logger.warning(str(e))
        return flask.Response(str(e), status=e.code, mimetype="text/plain")
    except Exception as e:
        app.logger.exception(
            "CSV generation failure! " + str(e)
        )
        raise
    #return app.response_class(status = 501, mimetype = "text/html")



@app.route('/csv/housekeeping', methods=['GET'])
def housekeeping_csv():
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
    except api.ApiException as e:
        app.logger.warning(str(e))
        return flask.Response(str(e), status=e.code, mimetype="text/plain")
    except Exception as e:
        app.logger.exception(
            "CSV generation failure! " + str(e)
        )
        raise
    #return app.response_class(status = 501, mimetype = "text/html")


@app.route('/csv/note', methods=["GET"])
def note_csv():
    """Export operator notes into a CSV file.

    Accepted request parameters:
    begin - PATE timestamp
    end - PATE timestamp

    Request parameters are optional. 'being' and 'end' timestamps limit the
    result set to include only entries within specified datetimes."""
    log_request(request)
    try:
        from api.Note import Note
        return api.stream_result_as_csv(Note(request).query())
    except api.ApiException as e:
        app.logger.warning(str(e))
        return flask.Response(str(e), status=e.code, mimetype="text/plain")
    except Exception as e:
        app.logger.exception(
            "CSV generation failure! " + str(e)
        )
        raise



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
            docstring = docstring.replace('<', '&lt;').replace('>', '&gt;')
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



###############################################################################
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
def send_ui(path = 'index.html'):
    """Send static HTML/CSS/JS/images/... content."""
    log_request(request)
    return send_from_directory('ui', path)



# EOF
