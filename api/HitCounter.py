#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Class for PATE Hit Counter Data
#
# HitCounter.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.20  Initial version.
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
import time
import logging
import sqlite3

from flask              import g
from pmapi              import app
from pmapi              import version

class HitCounter:

    @staticmethod
    def __column_list(cursor, table, exclude = []):
        """Method that compiles a list of data columns from a table"""
        sql = "SELECT * FROM {} LIMIT 1".format(table)
        # Ignore query result
        cursor.execute(sql)
        # ...and use cursor.description instead
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
        # Query preparations
        try:
            # Start timing
            t_real_start = time.perf_counter()
            t_cpu_start  = time.process_time()
            cursor = g.db.cursor()
            # Extract request parameters
            timestamp   = request.args.get('timestamp',   None, type=int)
            begin       = request.args.get('begin',       None, type=int)
            end         = request.args.get('end',         None, type=int)
            status = "(unspecified)"
            # Parse SQL for 'scidata'
            sql_packet = "SELECT packet_id, obc_timestamp FROM scidata "
            if timestamp:
                sql_packet += "WHERE obc_timestamp = :timestamp"
            elif begin and not end:
                sql_packet += "WHERE obc_timestamp >= :begin"
            elif end and not begin:
                sql_packet += "WHERE obc_timestamp <= :end"
            elif begin and end:
                sql_packet += "WHERE obc_timestamp >= :begin AND obc_timestamp <= :end"
            # Bind variables for 'scidata' query
            bvars = {'timestamp' : timestamp, 'begin' : begin, 'end' : end}
            # Parse SQL for 'classified'
            cols = HitCount.__column_list(
                cursor,
                table = 'classified',
                exclude = ['packet_id']
            )
            sql_hits =  "SELECT " + ",".join(cols) + \
                        " FROM classified WHERE packet_id = :packet_id"
        except:
            app.logger.exception("Query preparations failed!")
            raise
        # Execute query for Science Data packets
        try:
            # .fetchall() so that sub-loop query won't destroy results
            cursor.execute(sql_packet, bvars)
            packets = cursor.fetchall()
        except sqlite3.Error as e:
            app.logger.exception(
                "SQL='{}', bvars='{}'"
                .format(sql_packet, bvars)
            )
            raise

        # <n> rows from 'scidata' table retrieved. Use 'scidata.packet_id'
        # to retrieve data for sectors (and sun pointing telescope).
        data = []
        try:
            for packet_id, obc_timestamp in packets:
                bvars = {'packet_id' : packet_id}
                datapacket = {'timestamp' : obc_timestamp}
                app.logger.debug("Querying packet_id: {packet_id}".format(**bvars))
                # Query sectors
                result = cursor.execute(sql_hits, bvars)
                sectors = [dict(zip([key[0] for key in cursor.description], row)) for row in result]
                # Compile datapacket
                for sector in sectors:
                    # insert/add dict kval {<sector> : { 'e00' : <n>, ... }}
                    datapacket[sector['sector']] = {
                        key : value for key, value in sector.items() if key != 'sector'
                    }
                # Add to list of rows
                data.append(datapacket)

        except sqlite3.Error as e:
            # Log these, because in route.py exception handling they're gone
            app.logger.error(
                "SQL='{}', bvars='{}'"
                .format(sql_hits, bvars)
            )
            raise

        finally:
            # Cannot use 'cursor.rowcount' (it is always -1 with SQLite)
            info = {
                'version'   : version,      # imported from pmapi
                "t_cpu"     : time.process_time() - t_cpu_start,
                "t_real"    : time.perf_counter() - t_real_start,
                "rowcount"  : len(data),
            }
            cursor.close()
        return json.dumps({'jsonapi': info, 'data': data})
        # https://stackoverflow.com/questions/7907596/json-dumps-vs-flask-jsonify

# EOF
