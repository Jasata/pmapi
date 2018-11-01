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
#   0.2.1   2018.10.25  Added API Exception classes.
#   0.3.0   2018.10.29  Enhanced Flask.Response creation.
#
#
#   Module for PATE Monitor Resource Objects/Classes and API
#
#       API layout (endpoints/routes) are created in '/routes.py' file.
#       This directory contains the code that implements the interaction
#       between REST API calls and the database.
#
#   This file
#
#       api.response()
#
#       Turns a  ??? tuple (<data dictionary>, <HTTP response code>)
#       into a Flask.Response object (which is the expected return type
#       for route handles).
#
#   Resource Objects/Classes
#
#       Objects implement following public CRUD functions (if supporting):
#       (C) .post()     POST (create entity)
#       (R) .get()      GET (fetch-type)
#       (R) .search()   GET (search-type)
#       (U) .patch()    PATCH and PUT (update entity)
#       (D) .delete()   DELETE (delete specified entity)
#
#       All functions MUST return a tuple!
#       (<data dictionary>, <HTTP response code>)
#       Data dictionary may be None
#
import time
import json

from flask          import request
from flask          import g
from application    import app



#
# __make_response(code, payload)
# API internal / Generate Flask.Response from HTTP response code and data
# dictionary.
#
def __make_response(code, payload):
    """Generate Flask.Response from provided response code and dictionary."""
    assert(isinstance(payload, dict))
    try:
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
        # https://stackoverflow.com/questions/7907596/json-dumps-vs-flask-jsonify
        t = time.perf_counter()
        payload = json.dumps(payload, indent=4, sort_keys=True, default=str)
        #payload = json.dumps(payload)
        app.logger.debug("REMOVE SORT! json.dumps(): {:.1f}ms".format((time.perf_counter() - t) * 1000))

        response = app.response_class(
            response    = payload,
            status      = code,
            mimetype    = 'application/json'
        )
        allow = [method for method in request.url_rule.methods if method not in ('HEAD', 'OPTIONS')]
        response.headers['Allow'] = ", ".join(allow)
        response.headers['Content-Type'] = 'application/json'
        #response.headers['Content-Type'] = 'application/vnd.api+json'
        app.logger.debug(
            "api.__make_response() normal exit. code: {}, payload={}"
            .format(response.status, response.response)
        )
        return response
    except Exception as e:
        # VERY IMPORTANT! Do NOT re-raise the exception!
        app.logger.exception("Internal __make_response() error!")
        # We will try to offer dict instead of Flask.Response...
        return app.response_class(
            response = "api.__make_response() Internal Error: {}".format(str(e)),
            status   = 500
        )
        #    '{{"error": "api.response(): {}"}}'.format(str(e), )
        #return '''{{
        #    "error"     : "Internal Error",
        #    "details"   : "{}"
        #    }}'''.format(str(e))



#
# api.response(code, payload)
# JSON Flask.Response create function for Flask route handlers
#
def response(response_tuple):
    """Create Flask.Response from provided (code, dict) tuple."""
    return __make_response(response_tuple[0], response_tuple[1])


#
# api.exception_response(ApiException | Exception)
# Exception handling function for Flask route handlers
#
#   Generate payload dictionary from the ApiException or Exception object
#   and return through __make_response(), which generates the Flask.Response
#   object.
#
def exception_response(ex):
    """Generate JSON payload from ApiException or Exception object."""
    if not ex:
        app.logger.error("Function received arguemnt None!")
        return __make_response(
            500,
            {
                "error"   : "Unknown",
                "details" : "api.exception_response() received None!"
            }
        )
    # 
    try:
        if isinstance(ex, Exception):
            # Member variable '.ApiException' reveals the type
            if getattr(ex, 'ApiException', None):
                app.logger.error(
                    "ApiException: '{}'"
                    .format(str(ex))
                )
                response_code = ex.code
                response_payload = ex.to_dict()
            else:
                # Unexpected error, log trace by using logger.exception()
                app.logger.exception(str(ex))
                from traceback import format_exception
                e = format_exception(type(ex), ex, ex.__traceback__)
                response_payload = {
                    "error" : e[-1],
                    "trace" : "".join(e[1:-1])
                }
                response_code = 500
            return __make_response(response_code, response_payload)
        else:
            return __make_response(
                500,
                {
                    "error"     : "Uknown",
                    "details"   : "api.exception_response() received unsupported argument",
                    "type"      : type(ex)
                }
            )
    except Exception as e:
        app.logger.exception("Internal Error!")
        return __make_response(
            500,
            {
                "error"     : "Internal Error",
                "details"   : "api.exception_response() internal failure!"
            }
        )



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
# Combination of URI and method is not supported
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
# Route exists, implementation does not
# For request to something that is not planned, return 405
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
