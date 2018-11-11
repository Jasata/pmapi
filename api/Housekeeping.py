#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Class for PATE Hosekeeping Data
#
# Housekeeping.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.11.05  Initial version.
#
#
#   Housekeeping data is still unspecified. TBA.
#
#
import json
import logging
import sqlite3

from flask              import g
from application        import app
from .                  import InvalidArgument
from .                  import DataObject

class Housekeeping(DataObject):

    # Class variables
    sql         = ""
    args        = {}
    cursor      = None

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
        super().__init__(self.cursor, 'housekeeping')
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
                    # Replace with api.ApiException
                    raise InvalidArgument(
                        "Argument extraction failed!",
                        {'arguments' : request.args, 'exception' : str(e)}
                    ) from None

                # Convert to desired types (or create as None's)
                self.args.fields     = fields.split(',') if fields     else None
                self.args.timestamp  = int(timestamp)    if timestamp  else None
                self.args.begin      = int(begin)        if begin      else None
                self.args.end        = int(end)          if end        else None
                self.args.session_id = int(session_id)   if session_id else None

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


    def query(self, aggregate=None):
        """Processes HTTP Request arguments and executes the query.
        Returns SQLite3.Cursor object (DataObject requirement)."""
        #
        # Prepare SQL Statement
        #
        try:
            # api/__init__.py:DataObject().get_column_objects()
            cols = self.get_column_objects(
                include = self.args.fields or [],
                exclude=['session_id']
            )

            #
            # In aggregate request, drop primary key(s).
            # Use aggregate function only for INTEGER or REAL columns.
            #
            columnlist = []
            if aggregate:
                for col in cols:
                    if not col.primarykey:
                        if col.datatype in ('INTEGER', 'REAL'):
                            columnlist.append(
                                "{0}({1}) as {1}".format(aggregate, col.name)
                            )
                        else:
                            columnlist.append(
                                self.select_typecast(col)
                            )
            else:
                # No aggregate defined
                columnlist = [self.select_typecast(col) for col in cols]

            self.sql = "SELECT "
            self.sql += ", ".join(columnlist)
            self.sql +=" FROM housekeeping"

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
                "Query failure! SQL='{}', args='{}'"
                .format(self.sql, self.args)
            )
            raise

        # Must not close the cursor!
        return self.cursor



    def get(self, aggregate=None):
        """Handle Fetch and Search requests."""
        cursor = self.query(aggregate)

        #
        # Convert to dict or list of dicts
        #
        if self.args.timestamp or aggregate:
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

        #
        # Return as tuple
        #
        fields = self.args.pop('fields', None)
        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : self.args,
                        "fields"    : fields or "ALL"
                    }
                }
            )
        else:
            return (200, {"data": data})




# EOF
