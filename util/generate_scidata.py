#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# PATE Monitor / Development Utility 2018
#
# generate_scidata.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.20  Initial version.
#
import os
import time
import random
import sqlite3

class Config:
    db_file     = "pmapi.sqlite3"
    interval    = 15   # in seconds
    rotations   = 600
    max_hits    = 2**20

def generate_sector(packet_id, sector):
    def hits():
        return random.randint(0, Config.max_hits)
    return {
        'packet_id' : packet_id,
        'sector'    : sector,
        'e00'       : hits(),
        'e01'       : hits(),
        'e02'       : hits(),
        'e03'       : hits(),
        'e04'       : hits(),
        'e05'       : hits(),
        'e06'       : hits(),
        'e07'       : hits(),
        'p00'       : hits(),
        'p01'       : hits(),
        'p02'       : hits(),
        'p03'       : hits(),
        'p04'       : hits(),
        'p05'       : hits(),
        'p06'       : hits(),
        'p07'       : hits(),
        'p08'       : hits(),
        'p09'       : hits(),
        'p10'       : hits(),
        'p11'       : hits(),
        'ac'        : hits(),
        'dx0'       : hits(),
        'dx1'       : hits(),
        'dx2'       : hits(),
        'dx3'       : hits(),
        'trash0'    : hits(),
        'trash1'    : hits()
    }


if __name__ == '__main__':
    connection = sqlite3.connect(Config.db_file)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = 1")

    sql_scidata = """
    INSERT INTO scidata
    (
        obc_timestamp
    )
    VALUES
    (
        :obc_timestamp
    )
    """
    sql_classified = """
    INSERT INTO classified
    (
        packet_id,
        sector,
        e00,
        e01,
        e02,
        e03,
        e04,
        e05,
        e06,
        e07,
        p00,
        p01,
        p02,
        p03,
        p04,
        p05,
        p06,
        p07,
        p08,
        p09,
        p10,
        p11,
        ac,
        dx0,
        dx1,
        dx2,
        dx3,
        trash0,
        trash1
    )
    VALUES
    (
        :packet_id,
        :sector,
        :e00,
        :e01,
        :e02,
        :e03,
        :e04,
        :e05,
        :e06,
        :e07,
        :p00,
        :p01,
        :p02,
        :p03,
        :p04,
        :p05,
        :p06,
        :p07,
        :p08,
        :p09,
        :p10,
        :p11,
        :ac,
        :dx0,
        :dx1,
        :dx2,
        :dx3,
        :trash0,
        :trash1
    )
    """
    # Clear tables
    cursor.execute("DELETE FROM classified")
    cursor.execute("DELETE FROM scidata")
    connection.commit()

    obc_timestamp = int(time.time())
    for i in range(0, Config.rotations):
        cursor.execute(
            sql_scidata,
            {'obc_timestamp' : obc_timestamp + i * Config.interval}
        )
        packet_id = cursor.lastrowid
        for s in range(0, 37):
            print(
                "Rotation {:>4}, sector {:>2}"
                .format(i, s)
            )
            data = generate_sector(packet_id, s)
            cursor.execute(
                sql_classified,
                data
            )

    connection.commit()
    connection.close()

# EOF