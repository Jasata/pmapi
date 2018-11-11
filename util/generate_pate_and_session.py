#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PATE Monitor / Development Utility 2018
#
# generate_pate_and_session.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.11.11  Initial version.
#
import os
import sys
import time
import random
import sqlite3

from pathlib import Path


def get_session(cursor):
    """Get or create session. Also creates PATE, if needed."""

if __name__ == '__main__':

    filename = "../pmapi.sqlite3"
    dbfile = Path(filename)
    if not dbfile.is_file():
        print(filename, "not found!")
        os._exit(-1)

    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = 1")


    #
    # Get session, if available
    #
    row = cursor.execute("SELECT id FROM testing_session LIMIT 1").fetchone()
    if row:
        print(row[0])
    #
    # No testing_session rows, create one
    #
    row = cursor.execute("SELECT id FROM pate LIMIT 1").fetchone()
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
    conn.commit()
    print(cursor.lastrowid)

# EOF