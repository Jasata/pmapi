#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PATE Monitor / Development Utility 2018
#
# generate_housekeeping.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.11.05  Initial version.
#
# https://www.sqlite.org/limits.html
# SQLITE_MAX_SQL_LENGTH     Default is 1'000'000.
# SQLITE_MAX_COLUMN         Default is     2'000.
#
#   
import os
import sys
import time
import random
import sqlite3

class Config:
    db_file     = "pmapi.sqlite3"
    table_name  = "housekeeping"
    interval    = 60   # in seconds
    samples     = 1000 # one day of data
    max_hits    = 2**20

def get_column_list(cursor, table, exclude = []):
    """Method that compiles a list of data columns from a table"""
    if not exclude:
        exclude = []
    sql = "SELECT * FROM {} LIMIT 1".format(table)
    cursor.execute(sql)
    # Ignore query result and use cursor.description instead
    return [key[0] for key in cursor.description if key[0] not in exclude]


def generate_sql(cursor):
    sql1 = "INSERT INTO {} (timestamp, session_id, ".format(Config.table_name)
    sql2 = ") VALUES (?, ?, "
    cols = get_column_list(cursor, Config.table_name, ['timestamp', 'session_id'])
    sql_binds = ""
    for col in cols:
        sql_binds += "?, "
    return sql1 + ",".join(cols) + sql2 + sql_binds[:-2] + ")"

def generate_packet(session_id, cursor):
    """Generate tuple"""
    # Timestamp
    try:
        (generate_packet.timestamp)
    except:
        generate_packet.timestamp = time.time()
    else:
        generate_packet.timestamp += Config.interval
    # Number of columns to provide data for
    try:
        (generate_packet.nvars)
    except:
        generate_packet.nvars = len(get_column_list(
            cursor,
            Config.table_name,
            ['timestamp', 'session_id']
        ))
    nvars = generate_packet.nvars
    lst = [random.randint(0, Config.max_hits) for x in range(0, nvars)]
    lst.insert(0, session_id)
    lst.insert(0, generate_packet.timestamp)
    return tuple(lst)


def get_session(cursor):
    """Get or create session. Also creates PATE, if needed."""
    #
    # Get session, if available
    #
    row = cursor.execute("SELECT id FROM testing_session LIMIT 1").fetchone()
    if row:
        return row[0]
    #
    # No testing_session rows, create one
    #
    row = cursor.execute("SELECT id FROM pate LIMITE 1").fetchone()
    if not row:
        # create pate
        cursor.execute("INSERT INTO pate (id_min, id_max, label) VALUES (0, 1000, 'Proto')")
        pate_id = cursor.lastrowid
    else:
        pate_id = row[0]
    # create testing_session
    cursor.execute(
        """
        INSERT INTO testing_session (started, pate_id, pate_firmware)
        VALUES (?, ?, 'FW ver.1.0')
        """,
        (time.strftime('%Y-%m-%d %H:%M:%S'), pate_id)
    )
    return cursor.lastrowid

#
# Commandline
#
if __name__ == '__main__':

    try:
        Config.samples = int(sys.argv[1])
    except:
        pass


    connection = sqlite3.connect(Config.db_file)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = 1")

    # Generate PATE and testing session
    session_id = get_session(cursor)

    # Clear table
    cursor.execute("DELETE FROM {}".format(Config.table_name))
    connection.commit()

    # SQL
    sql = generate_sql(cursor)
    # Generate sci data samples
    print("Creating {} samples of housekeeping data...".format(Config.samples))
    try:
        for i in range(0, Config.samples):
            print("\r{:>6.2f} % ...".format((100*i)/Config.samples), end='')
            cursor.execute(
                sql,
                generate_packet(session_id, cursor)
            )
    except:
        print(sql)
        raise
    print("\r100.00 %      ")


    connection.commit()
    connection.close()

# EOF
