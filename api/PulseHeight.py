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
#   0.3.0   2018.11.04  Complies with new DataObject pattern.
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
    def __get_pk(cursor, table):
        """Returns a list of primary key columns for the table.
        Potentially vulnerable to SQL injection - avoid using with user input!"""
        # pragma_table_info() column:
        # cid           Column ID number
        # name          Column name
        # type          INTEGER | DATETIME | ...
        # notnull       1 = NOT NULL, 0 = NULL
        # dflt_value    Default value
        # pk            1 = PRIMARY KEY, 0 = not
        cursor.execute(
            "SELECT name FROM pragma_table_info('{}') WHERE pk = 1;"
            .format(table)
        )
        return [row[0] for row in cursor]



    @staticmethod
    def __column_list(cursor, table, exclude = []):
        """Method that compiles a list of data columns from a table"""
        cursor.execute("SELECT * FROM {} LIMIT 1".format(table))
        # Ignore query result and use cursor.description instead
        return [key[0] for key in cursor.description if key[0] not in exclude]



    def __init__(self, request):
        """Parses request arguments."""
        try:
            if request.args:
                # Raise exception for request unsupported arguments
                for k, _ in request.args.items():
                    if k not in ('fields', 'begin', 'end', 'timestamp'):
                        raise InvalidArgument("Unsupported argument '{}'".format(k))
                try:
                    fields      = request.args.get('fields',    None)
                    timestamp   = request.args.get('timestamp', None)
                    begin       = request.args.get('begin',     None)
                    end         = request.args.get('end',       None)
                except Exception as e:
                    raise InvalidArgument(
                        "Argument parsing error",
                        {'arguments' : request.args, 'exception' : str(e)}
                    )

                # Convert to desired types
                self.fields     = fields.split(',') if fields    else None
                self.timestamp  = int(timestamp)    if timestamp else None
                self.begin      = int(begin)        if begin     else None
                self.end        = int(end)          if end       else None

        except Exception as e:
            raise InvalidArgument(
                "Parameter extraction failed!",
                str(e)
            )

    @staticmethod
    def query(request):
        """
        Return pulse height data in JSON format. Three allowed usages:
        1. (no arguments)   All records are returned
        2. timestamp        The record matching timestamp
        3. begin and/or end Return records that fall between begin and end
        'timestamp', 'begin' and 'end' are UNIX datetime stamps.
        """
        #
        # Prepare SQL Statement
        #
        try:
            cursor = g.db.cursor()
            # Generate selected columns list
            # NOTE: .session_id is largely for internal purposes and
            #       not needed among the results.
            cols = PulseHeight.__column_list(
                cursor,
                table   = 'pulseheight',
                exclude = ['session_id']
            )
            # If fields is defined, filter out the rest
            # (with the exception of primary key - that must always be included)
            if self.fields:
                primarykeys = PulseHeight.__get_pk(cursor, 'pulseheight')
                cols = [col for col in cols if col in self.fields or col in primarykeys]

            sql = "SELECT " + ",".join(cols) + " FROM pulseheight "
            if self.timestamp:
                sql += "WHERE timestamp = :timestamp"
            elif self.begin and not self.end:
                sql += "WHERE timestamp >= :begin"
            elif self.end and not self.begin:
                sql += "WHERE timestamp <= :end"
            elif self.begin and self.end:
                sql += "WHERE timestamp >= :begin AND timestamp <= :end"
            self.sql = sql
            # Execute query
            self.bvars = {
                'timestamp' : timestamp,
                'begin'     : begin,
                'end'       : end
            }
        except:
            app.logger.exception("Query preparations failed!")
            raise

        #
        # Execute query
        #
        try:
            cursor.execute(self.sql, self.bvars)
        except:
            app.logger.exception(
                "Query failure! SQL='{}', bvars='{}'"
                .format(self.sql, self.bvars)
            )
            raise


        # Mind not to close the cursor
        return cursor



    def get(self):
        cursor = self.query()
        # https://medium.com/@PyGuyCharles/python-sql-to-json-and-beyond-3e3a36d32853
        # turn result object into a list of row-dictionaries
        # (result-)table column names are used as keys in key-value pairs.
        data = [dict(zip([key[0] for key in cursor.description], row)) for row in result]

        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query details" : {
                        "sql"               : self.sql,
                        "bind variables"    : self.bvars,
                        "fields"            : self.fields or "ALL"
                    }
                }
            )
        else:
            return (200, {"data": data})



    def csv(self):
        # Simply return the cursor. Api will stream it out.
        return self.query()



# EOF
