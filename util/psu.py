#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Testing utility for REST API /api/psu endpoint.
#
# /util/psu.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.28  Initial version.
#
import json
import urllib.request

endpoint = "http://localhost/api/psu"

#'function': 'SET_VOLTAGE', 'value': (float)
#'function': 'SET_CURRENT LIMIT', 'value': (float)
#'function': 'SET_POWER', 'value': 'ON' | 'OFF'
data = {
    'function': 'SET_VOLTAGE',
    'value': 3.21
}


req = urllib.request.Request(endpoint)
req.add_header('Content-Type', 'application/json; charset=utf-8')
jsondata = json.dumps(data).encode('utf-8')   # needs to be bytes
req.add_header('Content-Length', len(jsondata))
print (jsondata)

response = urllib.request.urlopen(req, jsondata)
print(response)

# EOF