#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PATE Monitor / Development Utility 2018
#
# generate_hitcount.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.23  Initial version.
#
# https://www.sqlite.org/limits.html
# SQLITE_MAX_SQL_LENGTH     Default is 1'000'000.
# SQLITE_MAX_COLUMN         Default is     2'000.
#
import os
import sys
import time
import random
import sqlite3

class Config:
    db_file     = "pmapi.sqlite3"
    table_name  = "hitcount"
    interval    = 15   # in seconds
    rotations   = 600
    max_hits    = 2**20

def generate_sql():
    sql1 = "INSERT INTO {} (rotation, session_id, ".format(Config.table_name)
    sql2 = ") VALUES (?, ?, "
    cols = []
    for sector in range(0,37):
        for proton in range(1,13):
            cols.append("s{:02}p{:02}, ".format(sector, proton))
        for electron in range(1,9):
            cols.append("s{:02}e{:02}, ".format(sector, electron))
        cols.append("s{:02}ac, ".format(sector))
        for dx in range(1,5):
            cols.append("s{:02}dx{:01}, ".format(sector, dx))
        for trash in range(1,3):
            cols.append("s{:02}trash{:01}, ".format(sector, trash))
    for col in cols:
        sql1 += col
        sql2 += "?, "
    return sql1[:-2] + sql2[:-2] + ")"

def generate_packet(session_id):
    """Generate tuple"""
    try:
        (generate_packet.timestamp)
    except:
        generate_packet.timestamp = time.time()
    else:
        generate_packet.timestamp += Config.interval
    nvars = 37 * 27
    lst = [random.randint(0, Config.max_hits) for x in range(0, nvars)]
    lst.insert(0, session_id)
    lst.insert(0, generate_packet.timestamp)
    return tuple(lst)

def generate_pate():
    cursor.execute("INSERT INTO pate (id_min, id_max, label) VALUES (0, 1000, 'Proto')")
    return cursor.lastrowid

def generate_session(pate_id):
    cursor.execute(
        """
        INSERT INTO testing_session (started, pate_id, pate_firmware)
        VALUES (?, ?, 'FW ver.1.0')
        """,
        (time.strftime('%Y-%m-%d %H:%M:%S'), pate_id)
    )
    return cursor.lastrowid

if __name__ == '__main__':

    connection = sqlite3.connect(Config.db_file)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = 1")

    # Generate PATE and testing session
    session_id = generate_session(generate_pate())

    # SQL
    sql = generate_sql()
    # Clear table
    cursor.execute("DELETE FROM {}".format(Config.table_name))
    connection.commit()

    # Generate sci data rotations
    try:
        for i in range(0, Config.rotations):
            cursor.execute(
                sql,
                generate_packet(session_id)
            )
    except:
        print(sql)
        raise


    connection.commit()
    connection.close()

# EOF