#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware component
# API Command interface
#
# Command.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.12  Initial version.
#
import json
import logging
import sqlite3


from flask              import g
from application        import app
from .                  import InvalidArgument, NotFound
from .                  import DataObject

class Command(DataObject):

    accepted_request_arguments = ('id')
    class DotDict(dict):
        """dot.notation access to dictionary attributes"""
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__
        def __missing__(self, key):
            """Return None if non-existing key is accessed"""
            return None

    def __init__(self, request):
        """Parses request arguments."""
        self.cursor = g.db.cursor()
        super().__init__(self.cursor, 'command')

        try:
            # build empty arg dictionary
            self.args = self.DotDict()
            for var in self.accepted_request_arguments:
                setattr(self.args, var, None)

            if request.args:
                # Raise exception for request unsupported arguments
                for key, _ in request.args.items():
                    if key not in self.accepted_request_arguments:
                        raise InvalidArgument(
                            "Unsupported argument '{}'".format(key)
                        )

                try:
                    id = request.args.get('id', None)
                except Exception as e:
                    # Replace with api.ApiException
                    raise InvalidArgument(
                        "Argument extraction failed!",
                        {'arguments' : request.args, 'exception' : str(e)}
                    ) from None

                self.args.id = int(id) if begin else None

        except InvalidArgument:
            raise
        except Exception as e:
            # Replace with api.ApiException
            raise InvalidArgument(
                "Parameter parsing failed!",
                str(e)
            ) from None

        #
        # JSON, if any
        #
        app.logger.debug(request.json)
        self.payload_json = request.json



    def query(self):
        """Fetch request ONLY!"""
        #
        # Complain 'id' is missing, because we support fetch requests only
        #
        if not self.args.id:
            raise InvalidArgument(
                "Missing mandatory 'id' query parameter!",
                "This interface supports only fetch-type requests, which require the command 'id' to be specified."
            )
        # SQL
        self.sql = "SELECT * FROM command WHERE id = :id"

        #
        # Execute query
        #
        try:
            self.cursor.execute(self.sql, self.args)
        except:
            app.logger.exception(
                "Query failure! SQL='{}', args='{}'"
                .format(self.sql, self.args)
            )
            raise

        return self.cursor

    def get(self):
        """Handle Fetch and Search requests."""
        cursor = self.query()
        result = cursor.fetchall()
        if len(result) < 1:
            raise NotFound(
                "Specified command not found!",
                "Provided command id '{}' does not match any in the database"
                .format(self.args.id)
            )
        data = dict(zip([c[0] for c in cursor.description], result[0]))

        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : self.args,
                        "fields"    : None
                    }
                }
            )
        else:
            return (200, {"data": data})

    def post(self, interface, command):
        """Enter new command into the database."""
        cmd2val = {
            "SET VOLTAGE"       : "voltage",
            "SET CURRENT LIMIT" : "limit",
            "SET POWER"         : "power"
        }
        if command not in cmd2val:
            # Programmer's error
            raise ValueError(
                "Unsupported command '{]'"
                .format(command)
            )
        #
        # Extract JSON parameters
        #
        if not self.payload_json:
            raise InvalidArgument(
                "This method requires a JSON payload!"
            )
        try:
            value = self.payload_json.get(cmd2val[command])
        except Exception as e:
            raise InvalidArgument(
                "Extracting JSON Parameter '{}' failed!"
                .format(cmd2val[command]),
                str(e)
            ) from None

        # Active session_id provided by /api/__init__.py:DataObject()
        self.sql = """
        INSERT INTO command (
            session_id,
            interface,
            command,
            value
        )
        VALUES (
            :session_id,
            :interface,
            :command,
            :value
        )
        """
        bvars = {
            "session_id"    : self.session_id,
            "interface"     : interface,
            "command"       : command,
            "value"         : value
        }
        try:
            cursor = g.db.cursor()
            cursor.execute(self.sql, bvars)
            g.db.commit()
        except:
            app.logger.exception(
                "Insert failure! SQL='{}', bvars='{}'"
                .format(self.sql, bvars)
            )
            raise

        #
        # Return
        #
        if app.config.get("DEBUG", False):
            return (
                202,
                {
                    "command_id"    : cursor.lastrowid,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : bvars,
                        "fields"    : None
                    }
                }
            )
        else:
            return (202, {"command_id": cursor.lastrowid})



# EOF