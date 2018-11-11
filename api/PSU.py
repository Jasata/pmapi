#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Class for PATE Monitor's testing PSU command interface
#
# PSU.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.27  Initial version.
#   0.2.0   2018.10.29  Complies to new api.response() specs.
#
#
# Command interface
#
#       method  'function'          'value' Description
#       GET     -                   -       Returns all values relevant to PSU.
#       POST    SET_POWER           ON|OFF  Set PSU power state ON or OFF.
#       POST    SET_VOLTAGE         float   Set PSU output voltage to 'val'.
#       POST    SET_CURRENT_LIMIT   float   Set PSU current limit to 'val'.
#
#       Example:
#           POST /api/psu HTTP/1.1
#           
#           {"function" : "SET_VOLTAGE", "value" : 3.3}
#
# PSU data
#
#       power               [ON | OFF]  PSU itself must obviously remain
#                                       powered, this represents the powerline
#                                       output. When toggling back to 'ON'
#                                       state, the PSU is required to remember
#                                       voltage and limit settings.
#       voltage_setting     float       Effective voltage setting.
#       current_limit       float       Effective current limit value.
#       measured_voltage    float       Measured output voltage.
#       measured_current    float       Measured output current.
#       state               string      'OK' or 'OVER CURRENT'.
#
# Functional notes
#
#       It is completely unknown how and under what conditions would the OBC
#       control the PSU (or even if it actually has any other control over
#       PATE than powering the unit ON and OFF - as it seems that PATE
#       consumes direct battery voltage).
#
#       This command interface does not concern itself with the actual
#       operating logic of the OBC. Instead, the PATE testing operator is
#       given these tools to manually alter operating voltage and toggle the
#       power.
#
# curl -i -X POST -H "Content-Type: application/json"" -d '{"function": "SET_VOLTAGE", "value": 3.21}' http://localhost/api/psu
#
import time
import logging
import sqlite3

from flask              import g
from application        import app
from .                  import InvalidArgument, Timeout, NotFound
from .                  import DataObject

class PSU(DataObject):

    accepted_request_arguments = ('fields')
    class DotDict(dict):
        """dot.notation access to dictionary attributes"""
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__
        def __missing__(self, key):
            """Return None if non-existing key is accessed"""
            return None

    # 500 ms result polling from 'command' table, before timeout
    polling_timeout = 0.5

    def __init__(self, request):
        """No need to parse - no request arguments supported"""
        self.cursor = g.db.cursor()
        super().__init__(self.cursor, 'psu')
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
                    fields      = request.args.get('fields',        None)
                except Exception as e:
                    # Replace with api.ApiException
                    raise InvalidArgument(
                        "Argument extraction failed!",
                        {'arguments' : request.args, 'exception' : str(e)}
                    ) from None

                # Convert to desired types (or create as None's)
                self.args.fields     = fields.split(',') if fields     else None

        except InvalidArgument:
            raise
        except Exception as e:
            # Replace with api.ApiException
            raise InvalidArgument(
                "Parameter parsing failed!",
                str(e)
            ) from None

        #
        # Complain if args.fields contains non-existent columns
        #
        if self.missing_columns(self.args.fields):
            raise InvalidArgument(
                "Non-existent fields defined!",
                "Field(s) " + ","
                .join(self.missing_columns(self.args.fields)) + " do not exist!"
            )



    def get(self, include=[]):
        """Retrieve and return 'psu' table row. The table either has no rows (backend is not running) or there is only one row."""

        try:
            self.sql = "SELECT "
            self.sql += self.select_columns(
                include=self.args.fields or include,
                exclude=["id"],
                include_primarykeys = False
            )
            self.sql += " FROM psu"
            try:
                self.cursor.execute(self.sql)
            except sqlite3.Error as e:
                app.logger.exception(
                    "psu -table query failed! ({})".format(self.sql)
                )
                raise
            else:
                # list of tuples
                result = self.cursor.fetchall()
                if len(result) < 1:
                    raise NotFound(
                        "No data in table 'psu'!",
                        "Most likely cause is that the OBC emulator is not running."
                    )
            # Create data dictionary from result
            data = dict(zip([c[0] for c in self.cursor.description], result[0]))
        finally:
            self.cursor.close()

        fields = self.args.pop('fields', None)
        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : None,
                        "fields"    : fields or "ALL"
                    }
                }
            )
        else:
            return (200, {"data": data})



    def post(self, request):
        """Support two PSU commands; 'voltage' and 'limit'. Each command
        takes one decimal argument (voltage or current). Accepted request
        parameters are thus, respective; 'fnc' and 'val'.
        
        Values are accepted with three decimal accuracy and decimals beyond
        those are simply truncated away.
        
        Middleware communicates to backend through the database's command
        table. This is asyncronous by definition and therefore this method
        shall poll the command table for an update that tells it if the
        command was successful or not. For obvious reasons, this activity
        has a timeout.
        
        Possible results:
        (406) InvalidArgument()         For any argument related issue.
        (200) {'result' : <str>}        On success.
        """
        try:
            if not request.json:
                raise InvalidArgument(
                    "API Request has no JSON payload!",
                    "This service requires 'function' and 'value' arguments."
                )
            # Extract parameters
            try:
                fnc     = request.json.get('function', None)
                val     = request.json.get('value',    None)
            except Exception as e:
                raise InvalidArgument(
                    "Argument parsing error",
                    {'request' : request.json, 'exception' : str(e)}
                )
            if not fnc or not val:
                raise InvalidArgument(
                    "Missing argument(s) 'function' and/or 'value'",
                    {'request' : request.json}
                )
            app.logger.debug("fnc='{}', val='{}'".format(fnc, val))

            #
            # Check parameters
            #
            if fnc in ("SET_VOLTAGE", "SET_CURRENT_LIMIT"):
                try:
                    val = float(val)
                except Exception as e:
                    raise InvalidArgument(
                        "Invalid 'value' argument!",
                        {'request' : request.json, 'exception' : str(e)}
                    )

            elif fnc == "SET_POWER":
                if val not in ("ON", "OFF"):
                    raise InvalidArgument(
                        "Invalid 'value', use 'ON' or 'OFF'!",
                        {'request' : request.json}
                    )

            else:
                raise InvalidArgument(
                    "Unrecognized 'function'!",
                    {'request' : request.json}
                )

            #
            # Execute function
            #
            sql = """
            INSERT INTO command
            (
                session_id,
                interface,
                command,
                value
            )
            VALUES
            (
                :session_id,
                'PSU',
                :command,
                :value
            )
            """
            try:
                cursor = g.db.cursor()
                # TODO: Solve testing session ID issue
                # Now just hardcoded for 1
                app.logger.critical("FIX SESSION ID ISSUE!!")
                bvars = {
                    'session_id'    : 1,
                    'command'       : fnc,
                    'value'         : str(val)
                }
                cursor.execute(sql, bvars)
                command_id = cursor.lastrowid
            except Exception as e:
                app.logger.exception(
                    "command -table INSERT failed! (sql='{}', bvars='{}')"
                    .format(sql, str(bvars))
                )
                raise
            app.logger.debug("command_id: '{}'".format(command_id))

            #
            # Command has been placed, poll for a result for timeout seconds
            #
            # NOTE: application.py makes sure these configuration values exist
            timeout  = app.config['COMMAND_TIMEOUT']
            interval = app.config['COMMAND_POLL_INTERVAL']

            result_sql = """
            SELECT  result
            FROM    command
            WHERE   id = {}
                    AND
                    result IS NOT NULL
            """.format(command_id)
            result = None
            end_time = time.time() + timeout
            while not result:
                result = cursor.execute(result_sql).fetchone()
                if time.time() > end_time:
                    break
            try:
                cursor.close()
            except:
                pass

            # Timeout?
            if not result:
                raise Timeout(
                    "PSU command timeout!",
                    {
                        'command.id' : command_id,
                        'sql' : sql,
                        'bvars' : bvars,
                        'request' : request.json,
                        'command_timeout' : timeout,
                        'command_poll_interval' : interval
                    }
                )
            # We have a result!
            return (200, {'result' : result})
        except Exception as e:
            app.logger.exception(
                "Error while processing PSU command!"
            )
            raise

# EOF
