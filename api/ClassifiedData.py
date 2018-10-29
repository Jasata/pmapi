#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Class for PATE Hit Counter Data
#
# ClassifiedData.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.20  Initial version.
#   0.2.0   2018.10.29  Complies to new api.response() specs.
#
#
#   Hit counter values for energy and type classified (by PATE).
#   Data exists in "rotations" (satellite rotates roughly once every
#   15 seconds). Each of these 360 degree rotations are divided into
#   10 degree sectors and each sector has its own set of hit counters.
#   In addition to the 36 sectors, there is 37th "sector" of hit counters
#   from the sun-pointing telescope.
#
#   Rotation is identified by timestamp (provided by PATE or OBC - TBD).
#   Rotation has 37 sectors of hit counter data; index zero is the
#   sun-pointing telescope and the rest follow logically the rotational
#   direction.
#
#   Each sector has particle class counters (representing energy levels);
#       12 proton counters
#        8 electron counters
#        1 AC counter
#        4 DX counters
#        2 Trash counters
#   + undetermined "PHA structures" ?? (Ask Jarno)
#
#   Thus, each rotation has 27 counters * 37 sectors = 999 counters.
#   The default setting for SQLITE_MAX_COLUMN is 2000.
#   (https://www.sqlite.org/limits.html)
#
import json
import logging
import sqlite3

from flask              import g
from application        import app
from .                  import InvalidArgument

class ClassifiedData:

    @staticmethod
    def __column_list(cursor, table, exclude = []):
        """Method that compiles a list of data columns from a table"""
        if not exclude:
            exclude = []
        sql = "SELECT * FROM {} LIMIT 1".format(table)
        cursor.execute(sql)
        # Ignore query result and use cursor.description instead
        return [key[0] for key in cursor.description if key[0] not in exclude]

    @staticmethod
    def get(request):
        """
        Return hit counter data in JSON format. Three allowed usages:
        1. (no arguments)   All records are returned
        2. timestamp        The record matching timestamp
        3. begin and/or end Return records that fall between begin and end
        'timestamp', 'begin' and 'end' are UNIX datetime stamps.
        """
        # Extract parameters from JSON
        try:
            if request.json:
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

            else:
                # Basically, SELECT all rows
                timestamp   = None
                begin       = None
                end         = None
        except:
            app.logger.exception("Parameter extraction failed!")
            raise


        # Prepare SQL Statement
        try:
            cursor = g.db.cursor()
            # Generate selected columns list
            cols = ClassifiedData.__column_list(
                cursor,
                table = 'hitcount',
                exclude = ['session_id']
            )
            sql = "SELECT " + ",".join(cols) + " FROM hitcount "
            if timestamp:
                sql += "WHERE rotation = :timestamp"
            elif begin and not end:
                sql += "WHERE rotation >= :begin"
            elif end and not begin:
                sql += "WHERE rotation <= :end"
            elif begin and end:
                sql += "WHERE rotation >= :begin AND rotation <= :end"
            # Bind variables for the query
            bvars = {'timestamp' : timestamp, 'begin' : begin, 'end' : end}
        except:
            app.logger.exception("SQL parsing failed!")
            raise


        # Execute query
        try:
            result = cursor.execute(sql, bvars)
            # Convert result into a dictionary
            data = [dict(zip([key[0] for key in cursor.description], row)) for row in result]
        except:
            app.logger.exception(
                "Query failure! SQL='{}', bvars='{}'"
                .format(sql, bvars)
            )
            raise
        finally:
            cursor.close()

        # TODO: obey app.config["DEBUG"]
        return (200, {'data': data, 'debug': {'sql': sql, 'bind variables' : bvars}})
 
# EOF
