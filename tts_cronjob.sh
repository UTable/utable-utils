#!/bin/bash

# runs python script, and outputs log files to appropriate folder

python3.7 tts_cronjob.py > "local-data/logs/$(date "+%Y-%m-%d"_ttscron.log)"