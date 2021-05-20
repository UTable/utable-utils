#!/bin/bash

# runs python script, and outputs log files to appropriate folder

source ../backend/venv/bin/activate
python tts_cronjob.py > "local-data/logs/$(date "+%Y-%m-%d"_ttscron.log)"
