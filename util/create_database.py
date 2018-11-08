#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PATE Monitor / Development Utility 2018
#
# create_database.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.23  Initial version.
#   0.2.0   2018.10.30  Corrected hitcount table columns.
#
import os
import sqlite3

conn = sqlite3.connect('pmapi.sqlite3')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = 1")

def drop(table):
    try:
        cursor.execute("DROP TABLE {}".format(table))
    except:
        pass

#
# Drop in reverse order (foreign keys)
#
drop("note")
drop("command")
drop("register")
drop("pulseheight")
drop("hitcount")
drop("testing_session")
drop("pate")
drop("psu")


try:
    #
    #   pate
    #
    #       PATE instruments shall be identified via (specified) ADC channel
    #       that has a unique resistor, giving the unit a unique reading on
    #       that channel. Columns id_min and id_max define the range in which
    #       the value needs to be, in order for the unit to be identified as
    #       the one defined by the row.
    #
    sql = """
    CREATE TABLE pate
    (
        id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        id_min      INTEGER NOT NULL,
        id_max      INTEGER NOT NULL,
        label       TEXT NOT NULL
    )
    """
    cursor.execute(sql)

    #
    # testing_session
    #
    #       PATE firmware may change between sessions. It shall be queried
    #       from the instrument and recorded into the testing session.
    #
    sql = """
    CREATE TABLE testing_session
    (
        id              INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        started         DATETIME,
        pate_id         INTEGER NOT NULL,
        pate_firmware   TEXT NOT NULL,
        FOREIGN KEY (pate_id) REFERENCES pate (id)
    )
    """
    cursor.execute(sql)

    #
    # hitcount
    #
    #       Science data (energy-classified particle hits) is collected in
    #       units of "rotations", as the satellite rorates over its axis.
    #       Each rotation is divided into 10 degree (36) sectors and each
    #       has the same collection of hit counts (12 + 8). In addition,
    #       there is "37th sector", which is in fact, the sun-pointing
    #       telescope.
    #
    #       Each sector has;
    #           10  Primary Proton energy classes (channels)
    #            7  Primary Electron energy classes
    #            2  Secondary Proton energy classes
    #            1  Secondary Electron energy class
    #
    #       Sector naming; sc[00..36], where sector zero is sun-pointing.
    #
    #       Both telescopes also collect other hit counters;
    #
    #            2  AC classes
    #            4  D1 classes
    #            1  D2 class
    #            2  trash classes
    #
    #       Telescope naming; st = Sun-pointing Telescope, rt = Rotating Telescope.
    #
    #       Design decision has been made to lay all these in a flat table,
    #       even though this generates more than a thousand columns.
    #
    #       Each row is identified by datetime value (named 'rotation') which
    #       designates the beginning of the measurement rotation. The start of
    #       each sector measurement is calculated based on 'rotation' timestamp
    #       and the rotation interval.
    #
    #       Sector zero (0) is the sun-pointing telescope, other indeces are
    #       naturally ordered with the rotational direction. (index 1 is
    #       measured first and index 36 last).
    #
    #       NOTE: Default limit for number of columns in SQLite is 2000
    #
    sql = """
    CREATE TABLE hitcount
    (
        rotation        DATETIME NOT NULL PRIMARY KEY,
        session_id      INTEGER NOT NULL,
    """
    cols = []
    # Sector specific counters
    for sector in range(0,37):
        for proton in range(1,13):
            cols.append("s{:02}p{:02} INTEGER NOT NULL, ".format(sector, proton))
        for electron in range(1,9):
            cols.append("s{:02}e{:02} INTEGER NOT NULL, ".format(sector, electron))
    # Telescope specfic counters
    for telescope in ('st', 'rt'):
        for ac in range(1, 3):
            cols.append("{}ac{} INTEGER NOT NULL, ".format(telescope, ac))
        # D1 hit patterns
        for d1 in range(1,5):
            cols.append("{}d1p{:01} INTEGER NOT NULL, ".format(telescope, d1))
        # D2 hit pattern
        cols.append("{}d2p1 INTEGER NOT NULL, ".format(telescope))
        for trash in range(1,3):
            cols.append("{}trash{:01} INTEGER NOT NULL, ".format(telescope, trash))
    sql += "".join(cols)
    sql += " FOREIGN KEY (session_id) REFERENCES testing_session (id) )"
    cursor.execute(sql)

    #
    # pulseheight
    #
    #       Calibration data is raw hit detection data from detector disks,
    #       containing ADC values that indicate the pulse heights.
    #
    #       Sample data contained an 8-bit hit mask. DOES THIS EXIST IN THE
    #       ACTUAL CALIBRATION DATA?
    #
    sql = """
    CREATE TABLE pulseheight
    (
        timestamp       DATETIME NOT NULL PRIMARY KEY,
        session_id      INTEGER NOT NULL,
        ac1             INTEGER NOT NULL,
        d1a             INTEGER NOT NULL,
        d1b             INTEGER NOT NULL,
        d1c             INTEGER NOT NULL,
        d2a             INTEGER NOT NULL,
        d2b             INTEGER NOT NULL,
        d3              INTEGER NOT NULL,
        ac2             INTEGER NOT NULL,
        FOREIGN KEY (session_id) REFERENCES testing_session (id)
    )
    """
    cursor.execute(sql)

    #
    # register
    #
    #       PATE Registers. Assumably, this table will get populated when
    #       a testing session begins, allowing UI to display these values
    #       without issuing (high-delay) commands to PATE for reading the
    #       values.
    #
    #       NOTE: Just a placeholder for now...
    #
    sql = """
    CREATE TABLE register
    (
        pate_id         INTEGER NOT NULL,
        retrieved       DATETIME NOT NULL,
        reg01           INTEGER NOT NULL,
        reg02           INTEGER NOT NULL,
        FOREIGN KEY (pate_id) REFERENCES pate (id)
    )
    """
    cursor.execute(sql)


    #
    # note
    #
    #       Store operator issued notes during a testing session.
    #       (remove for mission-time EGSE)
    #
    sql = """
    CREATE TABLE note
    (
        timestamp       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP PRIMARY KEY,
        session_id      INTEGER NOT NULL,
        text            TEXT,
        FOREIGN KEY (session_id) REFERENCES testing_session (id)
    )
    """
    cursor.execute(sql)



    #
    # command
    #
    sql = """
    CREATE TABLE command
    (
        id              INTEGER         NOT NULL PRIMARY KEY AUTOINCREMENT,
        session_id      INTEGER         NOT NULL,
        interface       TEXT            NOT NULL,
        command         TEXT            NOT NULL,
        value           TEXT            NOT NULL,
        created         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
        handled         DATETIME        NULL,
        result          TEXT            NULL,
        FOREIGN KEY (session_id) REFERENCES testing_session (id)
    )
    """
    cursor.execute(sql)


    #
    # PSU (this table is supposed to have only zero or one rows)
    #
    sql = """
    CREATE TABLE psu
    (
        id                  INTEGER         NOT NULL DEFAULT 0 PRIMARY KEY,
        power               TEXT            NOT NULL,
        voltage_setting     NUMBER          NOT NULL,
        current_limit       NUMBER          NOT NULL,
        measured_current    NUMBER          NOT NULL,
        measured_voltage    NUMBER          NOT NULL,
        state               TEXT            NOT NULL,
        modified            TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT          single_row_chk  CHECK (id = 0),
        CONSTRAINT          power_chk       CHECK (power IN ('ON', 'OFF')),
        CONSTRAINT          state_chk       CHECK (state IN ('OK', 'OVER CURRENT'))
    )
    """
    cursor.execute(sql)
    # SQLite doesn't have "CREATE OR REPLACE"
    trg = """
    CREATE TRIGGER psu_ari
    AFTER UPDATE ON psu
    FOR EACH ROW
    BEGIN
        UPDATE psu
        SET    modified = current_timestamp
        WHERE  id = old.id;
    END;
    """
    cursor.execute(trg)


    #
    # Housekeeping
    #
    sql = """
    CREATE TABLE housekeeping
    (
        timestamp       DATETIME NOT NULL PRIMARY KEY,
        session_id      INTEGER NOT NULL,
    """
    cols = []
    # dummy columns
    for c in range(0,37):
        cols.append("s_c{:02} INTEGER NOT NULL, ".format(c))    # S: Sun-pointing
        cols.append("r_c{:02} INTEGER NOT NULL, ".format(c))    # R: Rotating
    sql += "".join(cols)
    sql += " FOREIGN KEY (session_id) REFERENCES testing_session (id) )"
    cursor.execute(sql)

except:
    print("Database creation failed!")
    print(sql)
    raise
finally:
    conn.close()

# EOF