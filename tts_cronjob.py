# tts (text to scrape) automation via cron job
# run this every week to account for updated data that could potentially arise

# runs the following sequence:
# 1: web-fetch/checkdate.py // checks dates and downloads necessary pdf data
# 2: pdf-mod/pdf2txt.py     // does what you think
# 3: pdf-mod/tts.py         // scrapes the text and sends to appropriate storage facilities (database, json files, etc.)

import os
import sys


# get_newest_date: gets the newest date in the dates json list, and returns it
def get_newest_date():
    from datetime import datetime
    import json 
    dates = None
    with open("./local-data/dates.json", "r") as fp:
        dates = json.load(fp)
        print(dates)
    
    keys = []
    vals = []
    for key, val in dates.items():
        date = datetime.strptime(val, "%Y-%m-%d")
        keys.append(key)
        vals.append(date)
    
    i = vals.index(max(vals))
    return keys[i] 

# script_glue: combines all the python scripts to run via OS
def script_glue():
    date = get_newest_date()

    os.chdir('web-fetch')
    print("current working directory is: ", os.getcwd())
    os.system(f'{PYTHON_VER} checkdate.py')
    os.chdir('../pdf-mod')
    os.system(f"{PYTHON_VER} pdf2txt.py {date}.pdf > ../local-data/{date}.txt")
    os.system(f"{PYTHON_VER} tts.py {date}.txt -gd -dj -sd -c")

if __name__ == "__main__":
    script_glue()