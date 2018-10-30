#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Class for PATE Pulse Height Data
#
# PulseHeight.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#   0.1.1   2018.10.12  Added into.details, bug fixes.
#   0.1.2   2018.10.13  Changed to named SQL parameters (simpler to read).
#   0.2.0   2018.10.29  Complies to new api.response().
#
#
import json
import logging
import sqlite3

# Note on importing: THIS file has been imported by the application and thus
# the CWD is still application root ('/'). This is the reason why resources
# in subdirectories also include just as if they would run in root directory.
# (Because, these modules *ARE* running in the application root).
#
from flask              import g
from application        import app
from .                  import InvalidArgument

class PulseHeight:

    @staticmethod
    def get(request):
        """
        Return pulse height data in JSON format. Three allowed usages:
        1. (no arguments)   All records are returned
        2. timestamp        The record matching timestamp
        3. begin and/or end Return records that fall between begin and end
        'timestamp', 'begin' and 'end' are UNIX datetime stamps.
        """
        try:
            if not request.json:
                raise InvalidArgument(
                    "API Request has no JSON payload!",
                    "This service requires arguments."
                )

            # Extract parameters
            try:
                timestamp   = request.json.get('timestamp', None)
                begin       = request.json.get('begin',     None)
                end         = request.json.get('end',       None)
            except Exception as e:
                raise InvalidArgument(
                    "Argument parsing error",
                    {'request' : request.json, 'exception' : str(e)}
                )

            # Convert to desired types
            timestamp   = int(timestamp) if timestamp else None
            begin       = int(begin)     if begin     else None
            end         = int(end)       if end       else None

            # Parse SQL
            sql = "SELECT * FROM sample_pulse_height_data "
            if timestamp:
                sql += "WHERE timestamp = :timestamp"
            elif begin and not end:
                sql += "WHERE timestamp >= :begin"
            elif end and not begin:
                sql += "WHERE timestamp <= :end"
            elif begin and end:
                sql += "WHERE timestamp >= :begin AND timestamp <= :end"
            # Execute query
            bvars = {'timestamp' : timestamp, 'begin' : begin, 'end' : end}

        except:
            app.logger.exception("Query preparations failed!")
            raise

        # Execute query
        try:
            cursor = g.db.cursor()
            result = cursor.execute(sql, bvars)
        except sqlite3.Error as e:
            app.logger.exception(
                "SQL='{}', bvars='{}'"
                .format(sql, bvars)
            )
            raise
        else:
            # https://medium.com/@PyGuyCharles/python-sql-to-json-and-beyond-3e3a36d32853
            # turn result object into a list of row-dictionaries
            # (result-)table column names are used as keys in key-value pairs.
            data = [dict(zip([key[0] for key in cursor.description], row)) for row in result]
        finally:
            cursor.close()

        # if app.config['DEBUG'] == True:
        return (200, {'data': data, 'debug': {'sql': sql, 'bind variables' : bvars}})


# EOF
