#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Class for Operator Notes in PATE Monitor 
#
# PSU.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.11.08  Initial version.
#
#   Accepts two request parameters (request.args):
#   begin       Timestamp
#   end         Timestamp
#
#   Entity ID (Primary Key field):
#   timestamp   Timestamp
#
#   Primary Key field is expected to be provided as an URI parameter;
#   /api/note/<int:timestamp>
#   Flask framework will extract the parameter and route handler shall
#   invoke Note.fetch(timestamp) to produce a reply containing the single
#   identified entity (note).
#
import time
import logging
import sqlite3

from flask          import g, request
from application    import app
from .              import InvalidArgument, NotFound
from .              import Table


class Note(Table):

    # Allow the inspection of SQL and variables after query()
    sql             = ""
    bvars           = {}
    # Request arguments
    begin           = None
    end             = None
    session_id      = None
    timestamp       = None      # note.timestamp is Primary Key
    # Request payload
    payload_json    = None

    def __init__(self, request):
        """Parse request parameters and initialize object. Primary key field 'timestamp' is not accepted as request parameter. It is expected to be provided as URI parameter and extracted by Flask framework. See member function .fetch() for example handler."""
        self.cursor = g.db.cursor()
        super().__init__(self.cursor, 'note')
        try:
            if request.args:
                # Check that all args supported
                for k, v in request.args.items():
                    if k not in ('begin', 'end', 'session_id'):
                        raise InvalidArgument(
                            "Unsupported argument '{}'".format(k)
                        )
                # Extract values
                try:
                    begin       = request.args.get('begin',         None)
                    end         = request.args.get('end',           None)
                    session_id  = request.args.get('session_id',    None)
                except Exception as e:
                    raise InvalidArgument(
                        "Argument parsing error",
                        {'arguments' : request.args, 'exception' : str(e)}
                    )

                # Convert to desired types
                self.begin      = int(begin)        if begin        else None
                self.end        = int(end)          if end          else None
                self.session_id = int(session_id)   if session_id   else None

            # request JSON payload, if any (for POST method .create() calls)
            self.payload_json = request.json

        except Exception as e:
            raise InvalidArgument(
                "Parameter extraction failed!",
                str(e)
            )


    def query(self):
        """Parse SQL and execute query. Returns a cursor."""
        try:
            #
            # Parse SQL
            #
            self.sql = "SELECT " + self.select_columns + " FROM note"
            conditions = []
            # Having primary key specified takes precedence over all others
            if self.timestamp:
                conditions.append(
                    self.where_condition('timestamp') + " = :timestamp"
                )
            else:
                if self.begin:
                    conditions.append(
                        self.where_condition('timestamp') + " >= :begin"
                    )
                if self.end:
                    conditions.append(
                        self.where_condition('timestamp') + " >= :end"
                    )
                if self.session_id:
                    conditions.append("session_id = :session_id")
            if conditions:
                self.sql += " WHERE " + " AND ".join(conditions)

            #
            # Bind variables
            #
            self.bvars = {
                'timestamp'     : self.timestamp,
                'begin'         : self.begin,
                'end'           : self.end,
                'session_id'    : self.session_id
            }
        except:
            app.logger.exception("Query preparations failed!")
            raise

        #
        # Execute query
        #
        try:
            self.cursor.execute(self.sql, self.bvars)
        except:
            app.logger.exception(
                "Query failure! SQL='{}', bvars='{}'"
                .format(self.sql, self.bvars)
            )
            raise


        return self.cursor



    def fetch(self, timestamp):
        """Retrieve single note, identified by PK (self.timestamp)."""
        self.timestamp = timestamp
        cursor = self.query()
        data = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor]

        if data:
            if len(data) > 1:
                raise NotFound(
                    "Note by timestamp '{}' yields multiple results!"
                    .format(timestamp)
                )
            #
            # Return according to app DEBUG setting
            #
            if app.config.get("DEBUG", False):
                return (
                    200,
                    {
                        "data"          : data[0],
                        "query details" : {
                            "sql"               : self.sql,
                            "bind variables"    : self.bvars,
                            "fields"            : "NOT_SUPPORTED"
                        }
                    }
                )
            else:
                return (200, {"data": data[0]})

        else:
            raise NotFound(
                "Note by timestamp '{}' not found!".format(timestamp)
            )


    def search(self):
        """Returns a list of notes, filtered by 'begin' and/or 'end'."""
        cursor = self.query()
        data = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor]

        #
        # Return according to app DEBUG setting
        #
        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query details" : {
                        "sql"               : self.sql,
                        "bind variables"    : self.bvars,
                        "fields"            : "NOT_SUPPORTED"
                    }
                }
            )
        else:
            return (200, {"data": data})



    def create(self):
        """Insert new note."""
        #app.logger.debug(request.json)
        if not self.payload_json:
            raise InvalidArgument(
                "This method requires a JSON payload!"
            )
        app.logger.critical("TODO: get_current_session()")
        session_id = 1

        #
        # Extract JSON parameters
        #
        try:
            text = self.payload_json.get('text')
        except Exception as e:
            raise InvalidArgument(
                "JSON Parameter extraction failed!",
                str(e)
            )

        #
        # INSERT
        #
        try:
            cursor = g.db.cursor()
            self.sql = """INSERT INTO note (session_id, text)
            VALUES (:session_id, :text)"""
            self.bvars = {
                'session_id'    : session_id,
                'text'          : text
            }
            cursor.execute(self.sql, self.bvars)
            # NOT the primary key! The row id
            self.timestamp = cursor.lastrowid
        except:
            app.logger.exception(
                "Insert failure! SQL='{}', bvars='{}'"
                .format(self.sql, self.bvars)
            )
            raise

        #
        # Return with queried new row
        #
        return self.fetch(self.timestamp)



# EOF
