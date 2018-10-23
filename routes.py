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
import json
import flask
import logging

from flask          import request
from flask          import Response
from flask          import send_from_directory
from flask          import abort
from application    import app


###############################################################################
#
# Static content
#
#   NOTE:   Nginx has been configured (see /etc/nginx/nginx.conf) to serve
#           files of certain suffixes (images, css, js) which are deemed to
#           be always static. IF THIS CHANGES, YOU NEED TO MODIFY nginx.conf!!
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
@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

@app.route('/img/<path:path>')
def send_img(path):
    return send_from_directory('img', path)



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

# Route handlers must use this function to return exception
# JSON structures to clients
def exception_json(ex):
    """Parse JSON for a /currently handled/ exception"""
    try:
        from traceback import format_exception
        e = format_exception(type(ex), ex, ex.__traceback__)
        return json.dumps({
            'api' : {
                'version' : app.apiversion
            },
            'error' : e[-1],
            'trace' : "".join(e[1:-1])
        })
    except Exception as e:
        return '{{"error": "exception_json(): {}"}}'.format(str(e))

@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
def get_index():
    app.logger.debug("Page '/' requested...")
    return '<HTML><BODY><H1>TO BE REPLACED</H1></BODY></HTML>'
    # return flask.render_template(
    #     'index.html',
    #     title='List of Instruments'
    # )


#
# Sample Pulse Height Data (to be calibration data?)
#
@app.route('/pulseheight', methods=['GET'])
def get_pulseheight():
    app.logger.debug(
        "GET '{}' request..."
        .format(request.url_rule.rule)
    )
    try:
        from api.PulseHeight import PulseHeight
        return PulseHeight.get(request)
    except Exception as e:
        app.logger.exception(
            "GET '{}' failed"
            .format(request.url_rule.rule)
        )
        return exception_json(e)
    else:
        app.logger.debug(
            "GET '{}' completed"
            .format(request.url_rule.rule)
        )

# Not sure if we want to implement OPTIONS...to-be-decided
@app.route('/pulseheight', methods=['OPTIONS'])
def options_pulseheight():
    app.logger.debug("Page '/pulseheight' OPTIONS request...")
    opts = {
        'GET'       : '',
        'GET'       : 'timestamp',
        'GET'       : 'from',
        'GET'       : 'to',
        'GET'       : 'from,to',
        'OPTIONS'   : ''
    }
    return json.dumps(opts)

#
# Science Data (hit counters)
#
@app.route('/hitcount', methods=['GET'])
def get_hitcounterdata():
    app.logger.debug(
        "GET '{}' request..."
        .format(request.url_rule.rule)
    )
    try:
        from api.HitCounter import HitCounter
        response = Response(
            response = HitCountData.get(request),
            status   = 200
        )
        # Setting mimetype = ... in the above DOES NOT modify header!
        response.headers['Content-Type'] = 'application/vnd.api+json'
        return response
    except Exception as e:
        app.logger.exception(
            "GET '{}' failed"
            .format(request.url_rule.rule)
        )
        return exception_json(e)
    else:
        app.logger.debug(
            "GET '{}' completed"
            .format(request.url_rule.rule)
        )

# Get path components as arguments
@app.route('/test/<code>', methods=['GET'])
def test(code):
    app.logger.debug("GET '{}' request...".format(request.url_rule.rule))
    try:
        (test.var_)
    except:
        try:
            # Contrary to examples, custom messages are NOT sent
            abort(500)
        except Exception as e:
            return str(e)
    else:
        return "Hello"

# EOF
