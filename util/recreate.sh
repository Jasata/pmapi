#!/bin/bash

python3 create_database.py
python3 generate_pate_and_session.py
python3 generate_hitcount.py 5760
python3 generate_housekeeping.py 300
python3 import_sample_pulseheight_data.py

