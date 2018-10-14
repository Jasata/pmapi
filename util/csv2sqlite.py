#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PATE Monitor / Development Utility 2018
#
# csv2sqlite.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#   0.1.1   2018.10.14  Cleaned for GitHub
#
#       This utility imports the provided pulse height data sample into a
#       SQLite database - to be made available via Flask REST API.
#
#
#       Zero-based index 20 is column "U" ('Status'). This script will insert
#       columns 20 thru 28.
import os
import csv
import time
import sqlite3

class Config:
    csv_file     = "sample.csv"
    db_file      = "pmapi.sqlite3"
    row_first    = time.time()      # Note: Python timestamp has microseconds (float)
    row_interval = 15               # in seconds

class excel_finnish(csv.Dialect):
    """Describe the properties of Finnish locale Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\r\n'
    quoting = csv.QUOTE_MINIMAL
csv.register_dialect("excel-finnish", excel_finnish)

if __name__ == '__main__':

    conn = sqlite3.connect(Config.db_file)
    curs = conn.cursor()

    # Create table (or fail gracefully, if already exists)
    sql_create_table = """
        CREATE TABLE IF NOT EXISTS sample_pulse_height_data (
            timestamp   INTEGER,
            hits        INTEGER,
            AC1         INTEGER,
            D1A         INTEGER,
            D1B         INTEGER,
            D1C         INTEGER,
            D2A         INTEGER,
            D2B         INTEGER,
            D3          INTEGER,
            AC2         INTEGER
        )
    """
    try:
        curs.execute(sql_create_table)
    except sqlite3.Error as e:
        print(e)
        os._exit(-1)

    sql_delete = """
        DELETE FROM sample_pulse_height_data
    """
    try:
        curs.execute(sql_delete)
    except sqlite3.Error as e:
        print(e)
        os._exit(-1)


    sql_insert = """
        INSERT INTO sample_pulse_height_data (
            timestamp,
            hits,
            AC1,
            D1A,
            D1B,
            D1C,
            D2A,
            D2B,
            D3,
            AC2
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
    """

    with open(Config.csv_file, 'r') as csvfile:
        reader = csv.reader(csvfile, dialect='excel-finnish')

        # Skip two first rows
        header = next(reader, None)
        header = next(reader, None)

        # Selected columns 20 - 28, range() is [a, b[ 
        included_cols = [x for x in range(20,29)]

        for index, row in enumerate(reader):
            # import pdb; pdb.set_trace()
            content = list(int(row[i], 2) if i == 20 else int(row[i]) for i in included_cols)

            curs.execute(
                sql_insert,
                (
                    int(Config.row_first + index * Config.row_interval),
                    content[0],
                    content[1],
                    content[2],
                    content[3],
                    content[4],
                    content[5],
                    content[6],
                    content[7],
                    content[8]
                )
            )
    conn.commit()

# EOF
