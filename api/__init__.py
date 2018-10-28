#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# API module
#
# api/__init__.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#   0.2.0   2018.10.23  Content moved to top-level application.py.
#   0.2.1   2018.10.25  Added API Exception classes
#
import time
import json
from application import app


from flask          import request
from flask          import g
from application    import app



#
# Create Flask.Response object for given payload
# (ApiException, Exception or dictionary)
#
def response(data, code=200):
    """Create Flask.Response object from data, which can be either
    a dictionary (normally) or an ApiException or Exception."""
    try:
        if not data:
            app.logger.critical("api.response(): data cannot be None!")
            raise ValueError("Argument 'data' cannot be None!")

        #
        # Test for acceptable input types
        #
        if isinstance(data, Exception):
            # Now we know 'data' is a class
            if getattr(data, 'ApiException', None):
                app.logger.error(
                    "ApiException: '{}'"
                    .format(str(data))
                )
                payload = data.to_dict()
                code = data.code
            else:
                app.logger.exception(str(data))
                from traceback import format_exception
                e = format_exception(type(data), data, data.__traceback__)
                payload = {
                    'error' : e[-1],
                    'trace' : "".join(e[1:-1])
                }
                code = 500

        elif isinstance(data, dict):
            payload = data

        else:
            raise ValueError("data argument was not any of the accepted types!")


        #
        # Common operations
        #
        payload['api'] = {
            'version'   : app.apiversion,
            't_cpu'     : time.process_time() - g.t_cpu_start,
            't_real'    : time.perf_counter() - g.t_real_start
        }
        # NOTE: PLEASE remove 'indent' and 'sort_keys' when developing is done!!!
        # 'default=str' is useful to handle obscure data, leave it.
        # (for example; "datetime.timedelta(31) is not JSON serializable")
        payload = json.dumps(payload, indent=4, sort_keys=True, default=str)

        response = app.response_class(
            response    = payload,
            status      = code,
            mimetype    = 'application/json'
        )
        allow = [method for method in request.url_rule.methods if method not in ('HEAD', 'OPTIONS')]
        response.headers['Allow'] = ", ".join(allow)
        response.headers['Content-Type'] = 'application/vnd.api+json'
        return response

    except Exception as e:
        # VERY IMPORTANT! Do NOT raise an exception,
        # or you risk a loop at route handlers
        app.logger.exception("api.response() error!")
        return '{{"error": "api.response(): {}"}}'.format(str(e), )


#
# Custom API error handler (registered at 'application.py')
#
#   Purpose of this is to catch "Not Found" cases for requests to '/api' and
#   return JSON API -style responses for them.
#
#   Other requests that are deemed not to be REST API calls, should be
#   responded to in a standard way (with 404 and HTML message payload).
#
#   THIS IS WORK IN PROGRESS! I will return to this at somepoint, if/when
#   I have time for it (because this is not so vital for this solution).
#
from werkzeug.exceptions import HTTPException
def custom_api_error_handler(ex):
    from flask import request
    if request.path[0:5] == "/api/":
        payload = {
            'type':         'InternalServerError',
            'description':  'Internal Error',
            'method':       request.method,
            'url':          request.url
        }
        if isinstance(exception, HTTPException):
            payload['type'] = 'HTTPException'
            payload['description'] = exception.description
            status_code = exception.code
        else:
            payload['description'] = exception.args
            status_code = 500
        return jsonify(payload), status_code
    else:
        return "bummer", 405


#
# Object code (code that interacts with database) exist as modules.
# (As separate Python files in this directory)
# Classes model data by providing CRUD interactions and returning
# data as dictionaries (or list of dictionaries, for searches)
# - or they raise ApiExceptions (see this file) when necessary.
#

#
# API Exception classes
#
class ApiException(Exception):

    # Used to identify objects based on ApiException and its subclasses.
    # Because, ...I don't know how a better way to do this.
    ApiException = True

    def __init__(
        self,
        message = "Unspecified API Error",  # as in Exception
        details = None                      # Any additional details
    ):
        """Initialize API Exception instance"""
        super().__init__(message)
        self.details = details

    def to_dict(self):
        """Return values of each fields of an jsonapi error"""
        error_dict = {'message' : str(self)}
        # Do not include 'code', because that is used as the response code
        if getattr(self, 'details', None):
            error_dict.update({'details' : getattr(self, 'details')})
        return error_dict


#
# Client side errors (4xx)
#

# 404 Not Found
class NotFound(ApiException):
    """Identified item was not found in the database."""
    def __init__(
        self,
        message = "Entity not found!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 404


# 405 Method Not Allowed
class MethodNotAllowed(ApiException):
    """Request method is not supported."""
    def __init__(
        self,
        message = "Requested method is not supported!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 405


# 406 Not Acceptable
class InvalidArgument(ApiException):
    """Provided argument(s) are invalid!"""
    def __init__(
        self,
        message = "Provided argument(s) are invalid!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 406


# 409 Conflict
class Conflict(ApiException):
    """Unique/PK,FK or other constraint violation."""
    def __init__(
        self,
        message = "Unique, primary key, foreign key or other constraint violation!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 409


#
# Server side errors (5xx)
#

# 500 Internal Server Error
class Timeout(ApiException):
    """Processing/polling exceeded allowed timeout."""
    def __init__(
        self,
        message = "Processing/polling exceeded allowed timeout!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 500


# 500 Internal Server Error
class InternalError(ApiException):
    """All other internal processing erros, except timeouts."""
    def __init__(
        self,
        message = "Unspecified internal processing error!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 500


# 501 Not Implemented
class NotImplemented(ApiException):
    """Requested functionality is not yet implemented."""
    def __init__(
        self,
        message = "Requested functionality is not yet implemented.",
        details = None
    ):
        super().__init__(message, details)
        self.code = 501



if __name__ == '__main__':

    try:
        raise NotFound("Not here!", {'bummer' : 2, 'fix' : None})
    except Exception as e:
        print(e.to_dict())
        print(e)

# EOF
