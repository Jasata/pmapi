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
#
#
import json
import time
import logging
import sqlite3

# Note on importing: THIS file has been imported by the application and thus
# the CWD is still application root ('/'). This is the reason why resources
# in subdirectories also include just as if they would run in root directory.
# (Because, these modules *ARE* running in the application root).
#
from flask              import g
from application        import app

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
        cursor = g.db.cursor()
        # Extract request parameters
        timestamp   = request.args.get('timestamp',   None, type=int)
        begin       = request.args.get('begin',       None, type=int)
        end         = request.args.get('end',         None, type=int)
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
        try:
            result = cursor.execute(sql, bvars)
        except sqlite3.Error as e:
            app.logger.exception(
                "SQL='{}', bvars='{}'"
                .format(sql, bvars)
            )
            data = []
        else:
            # https://medium.com/@PyGuyCharles/python-sql-to-json-and-beyond-3e3a36d32853
            # turn result object into a list of row-dictionaries
            # (result-)table column names are used as keys in key-value pairs.
            data = [dict(zip([key[0] for key in cursor.description], row)) for row in result]
        finally:
            cursor.close()

        # if app.config['DEBUG'] == True:
        return {'data': data, 'debug': {'sql': sql, 'bind variables' : bvars}}
        # else:
        #    return {'data': data}


# EOF