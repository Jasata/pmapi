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
#
#
import json
import time
import logging
import sqlite3

from flask              import g
from pmapi              import app

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
        # Start timing
        t_real_start = time.perf_counter()
        t_cpu_start  = time.process_time()
        cursor = g.db.cursor()
        # Extract request parameters
        begin = request.args.get('begin',       None, type=int)
        end   = request.args.get('end',         None, type=int)
        t     = request.args.get('timestamp',   None, type=int)
        # Parse SQL
        sql = """
            SELECT  *
            FROM    sample_pulse_height_data
        """
        bvars = tuple()
        if t:
            sql += """
                WHERE   timestamp = ?
            """
            bvars = (t,)
        elif begin or end:
            sql += "WHERE "
            if begin:
                sql += " timestamp >= ? "
                if end:
                    sql += " AND timestamp <= ?"
                    bvars = (begin, end)
                else:
                    bvars = (begin,)
            elif end:
                sql += " timestamp <= ?"
                bvars = (end,)
        # Execute query
        try:
            result = cursor.execute(sql, bvars)
        except sqlite3.Error as e:
            app.logger.exception(
                "SQL='{}', bvars='{}'"
                .format(sql, bvars)
            )
            status = "ERROR"
            data = []
            details = str(e)
        else:
            # https://medium.com/@PyGuyCharles/python-sql-to-json-and-beyond-3e3a36d32853
            # turn result object into a list of row-dictionaries
            # (result-)table column names are used as keys in key-value pairs.
            status = "OK"
            data = [dict(zip([key[0] for key in cursor.description], row)) for row in result]
            details = sql
        finally:
            info = {
                "t_cpu"     : time.process_time() - t_cpu_start,
                "t_real"    : time.perf_counter() - t_real_start,
                "rowcount"  : cursor.rowcount,
                "status"    : status,
                "details"   : details
            }
            cursor.close()
        return json.dumps({'info': info, 'data': data})

# EOF
