#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PATE Monitor / Development Utility 2018
#
# import_sample_pulseheight_data.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#   0.1.1   2018.10.14  Cleaned for GitHub
#   0.2.0   2018.11.11  Renamed. Saves to 'pulseheight' now.
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
    db_file      = "../pmapi.sqlite3"
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
    row = cursor.execute("SELECT id FROM pate LIMIT 1").fetchone()
    if not row:
        # create pate
        cursor.execute("INSERT INTO pate (id_min, id_max, label) VALUES (0, 1000, 'Created to insert sample pulseheight data')")
        pate_id = cursor.lastrowid
    else:
        pate_id = row[0]
    # create testing_session
    cursor.execute(
        """
        INSERT INTO testing_session (started, pate_id, pate_firmware)
        VALUES (?, ?, 'Created to insert sample pulseheight data')
        """,
        (time.strftime('%Y-%m-%d %H:%M:%S'), pate_id)
    )
    return cursor.lastrowid



if __name__ == '__main__':

    from pathlib import Path

    dbfile = Path(Config.db_file)
    if not dbfile.is_file():
        print(Config.db_file, "not found!")
        os._exit(-1)

    connection = sqlite3.connect(Config.db_file)
    cursor = connection.cursor()

    # First clear out existing data
    try:
        cursor.execute("DELETE FROM pulseheight")
    except sqlite3.Error as e:
        print(str(e))
        os._exit(-1)

    session_id = get_session(cursor)

    sql = """
        INSERT INTO pulseheight (
            timestamp,
            session_id,
            ac1,
            d1a,
            d1b,
            d1c,
            d2a,
            d2b,
            d3,
            ac2
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

            cursor.execute(
                sql,
                (
                    int(Config.row_first + index * Config.row_interval),
                    session_id,
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
    connection.commit()

# EOF
