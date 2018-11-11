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
#   0.3.1   2018.11.10  Improved query parsing.
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
from .                  import InvalidArgument, NotFound
from .                  import DataObject

class PulseHeight(DataObject):

    accepted_request_arguments = (
        'fields',
        'begin',
        'end',
        'timestamp',
        'session_id'
    )
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
        super().__init__(self.cursor, 'pulseheight')
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
                    timestamp   = request.args.get('timestamp',     None)
                    begin       = request.args.get('begin',         None)
                    end         = request.args.get('end',           None)
                    session_id  = request.args.get('session_id',    None)
                except Exception as e:
                    # Raise api.ApiException
                    raise InvalidArgument(
                        "Argument extraction failed!",
                        {'arguments' : request.args, 'exception' : str(e)}
                    )

                # Convert to desired types (or create as None's)
                self.args.fields     = fields.split(',') if fields     else None
                self.args.timestamp  = int(timestamp)    if timestamp  else None
                self.args.begin      = int(begin)        if begin      else None
                self.args.end        = int(end)          if end        else None
                self.args.session_id = int(session_id)   if session_id else None

        except Exception as e:
            # Raise api.ApiException
            raise InvalidArgument(
                "Parameter parsing failed!",
                str(e)
            )


    def query(self, aggregate=None):
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
            self.sql = "SELECT "
            # api/__init__.py:DataObject().select_columns()
            self.sql += self.select_columns(
                include = self.args.fields or [],
                exclude = ['session_id']
            )
            self.sql +=" FROM pulseheight "


            # if aggregate:
            #     # For aggregated queries, remove PK columns
            #     cols = ",".join([
            #         "{0}({1}) as {1}".format(aggregate, col)
            #         for col in self.columns if col not in self.primarykeys
            #     ])
            #     #for pk in primarykeys:
            #     #    cols.remove(pk)
            # else:
            #     cols = ",".join(cols)



            #
            # WHERE conditions
            #
            conditions = []
            if self.args.timestamp:
                # Fetch request. Ignore other conditions.
                conditions.append(
                    self.where_condition('timestamp') + " = :timestamp"
                )
            else:
                if self.args.begin:
                    conditions.append(
                        self.where_condition('timestamp') + " >= :begin"
                    )
                if self.args.end:
                    conditions.append(
                        self.where_condition('timestamp') + " <= :end"
                    )
                if self.args.session_id:
                    conditions.append("session_id = :session_id")
            if conditions:
                self.sql += " WHERE " + " AND ".join(conditions)

        except:
            app.logger.exception("Query preparations failed!")
            raise

        #
        # Execute query
        #
        try:
            self.cursor.execute(self.sql, self.args)
        except:
            app.logger.exception(
                "Query failure! SQL='{}', bvars='{}'"
                .format(self.sql, self.args)
            )
            raise


        # Mind not to close the cursor
        return self.cursor



    def get(self, aggregate=None):
        """Fetch and Search request handled."""
        cursor = self.query(aggregate)
        # https://medium.com/@PyGuyCharles/python-sql-to-json-and-beyond-3e3a36d32853
        # turn result object into a list of row-dictionaries
        # (result-)table column names are used as keys in key-value pairs.
        if self.args.timestamp:
            # Fetch request - return object
            result = cursor.fetchall()
            if len(result) < 1:
                raise NotFound(
                    "Pulseheight record not found!",
                    "Provided timestamp '{}' does not match any in the database"
                    .format(self.args.timestamp)
                )
            data = dict(zip([c[0] for c in cursor.description], result[0]))
        else:
            # Search request - return a list of objects
            data = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor]

        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query" : {
                        "sql"               : self.sql,
                        "bind variables"    : self.args,
                        "fields"            : self.args.fields or "ALL"
                    }
                }
            )
        else:
            return (200, {"data": data})



# EOF
