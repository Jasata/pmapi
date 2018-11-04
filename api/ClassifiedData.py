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

    # Query and bind variables
    sql         = ""
    bvars       = {}
    # Arguments
    fields      = None
    begin       = None
    end         = None
    timestamp   = None

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


    def query(self):
        """Processes HTTP Request arguments and executes the query.
        Returns SQLite3.Cursor object (DataObject requirement)."""
        #
        # Prepare SQL Statement
        #
        try:
            cursor = g.db.cursor()
            # Generate selected columns list
            # NOTE: .session_id is largely for internal purposes and
            #       not needed among the results.
            cols = ClassifiedData.__column_list(
                cursor,
                table   = 'hitcount',
                exclude = ['session_id']
            )
            # If fields is defined, filter out the rest
            # (with the exception of primary key - that must always be included)
            if self.fields:
                app.logger.debug("Filtering with '{}'".format(self.fields))
                primarykeys = ClassifiedData.__get_pk(cursor, 'hitcount')
                cols = [col for col in cols if col in self.fields or col in primarykeys]

            # Parse SQL statement
            sql = "SELECT " + ",".join(cols) + " FROM hitcount "
            if self.timestamp:
                sql += "WHERE rotation = :timestamp"
            elif self.begin and not self.end:
                sql += "WHERE rotation >= :begin"
            elif self.end and not self.begin:
                sql += "WHERE rotation <= :end"
            elif self.begin and self.end:
                sql += "WHERE rotation >= :begin AND rotation <= :end"
            self.sql = sql
            # Bind variables for the query
            self.bvars = {
                'timestamp' : self.timestamp,
                'begin'     : self.begin,
                'end'       : self.end
            }
        except:
            app.logger.exception("SQL parsing failed!")
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

        # Must not close the cursor!
        return cursor



    def get(self):
        """
        Return hit counter data in JSON format. Three allowed usages:
        1. (no arguments)   All records are returned
        2. timestamp        The record matching timestamp
        3. begin and/or end Return records that fall between begin and end
        'timestamp', 'begin' and 'end' are UNIX datetime stamps.
        """
        cursor = self.query()
        # Convert result into a dictionary
        data = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor]

        # NOTE: data is to be a list of dictionaries
        #return data, {"sql" : self.sql, "bind variables" : self.bvars}

        # TODO: obey app.config["DEBUG"]
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



    def csv():
        # Simply return the cursor. Api will stream it out.
        return self.query()


# EOF
