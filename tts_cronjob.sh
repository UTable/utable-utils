#!/bin/bash

# runs python script, and outputs log files to appropriate folder

./tts_cronjob.py > "$(date "+%Y-%m-%d"_ttscron.log)"