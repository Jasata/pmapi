#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
class ApiException(Exception):

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

class NotFound(ApiException):
    """Identified item was not found in the database."""
    def __init__(
        self,
        message = "Entity not found!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 404

def make_response(data, code=200):
    print("Response({},{})".format(data, code))


if __name__ == '__main__':
    try:
        raise NotFound("Not here!", {'bummer' : 2, 'fix' : None})
    except Exception as e:
        print(e.to_dict())
        print(e)
        # I don't seem to be able to check if an object is based on baseclass
        print(type(e))
        print("is instance of ApiException:", isinstance(e, type(ApiException)))
        print("is instance of Exception:", isinstance(e, type(Exception)))

    # Test unpacking
    res = ({'cat':'milk', 'dog':'bone'}, None)
    make_response(*res)

# EOF