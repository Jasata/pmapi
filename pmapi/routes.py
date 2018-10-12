#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware component
# Flask routes
#
# pmapi/routes.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#
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
import json
import flask
import logging

from flask      import request
from flask      import send_from_directory
from pmapi      import app

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
# Routes for dynamic content
#
@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
def get_index():
    app.logger.debug("Page '/' requested...")
    return '<HTML><BODY><H1>TO BE REPLACED</H1></BODY></HTML>'
    # return flask.render_template(
    #     'index.html',
    #     title='List of Instruments'
    # )


@app.route('/pulseheight', methods=['GET'])
def get_pulseheight():
    app.logger.debug("Page '/pulseheight' GET request...")
    try:
        from pmapi.PulseHeight import PulseHeight
        return PulseHeight.get(request)
    except Exception as e:
        app.logger.exception("Request handing failed")
        return str(e)
    #finally:
    #    app.logger.debug("Page '/pulseheight' completed")

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

# EOF
