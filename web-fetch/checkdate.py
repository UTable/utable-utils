#!/usr/local/bin/python3.8

"""
    Name: Bailey Chittle
    Date created: June 27 2020

    Program Description: checks date modified pdfs from a website, and 
        downloads the files in this directory if the date modified is different than the date stored here
"""

from bs4 import BeautifulSoup
from urllib import request
import re
import os
import json
from datetime import datetime

print("#########################################################################")

UWINPATH = 'https://www.uwindsor.ca'
TIMETABLE_PATH = '/registrar/541/timetable-information'
URLPATH = UWINPATH + TIMETABLE_PATH
DATADIR = '../data'
FILENAME = f'{DATADIR}/dates.json'

source = request.urlopen(URLPATH).read()
soup = BeautifulSoup(source, features='lxml')

p_tags = soup.find_all('p')
sub_p_tags = []
print(type(p_tags[0]))
for tag in p_tags:
    if 'Posted' in tag.text:
        sub_p_tags.append(tag)

p_tags = sub_p_tags
sub_p_tags = []

stored_dates = {} 
dates = {} 
if os.path.isfile(FILENAME):
    with open(FILENAME, 'rb') as fp:
        stored_dates = json.load(fp)

# converts string date to datetime obj
def convert_date(date):
    new_date = date.replace('/', '-')[2:]
    new_date = datetime.strptime(new_date, "%y-%m-%d")
    return new_date

def get_datename(basename):
    result = basename.replace("fall_", "f")
    result = result.replace("winter_", "w")
    result = result.replace("summer_", "s")
    return result[:5]

print("ptags: ", p_tags)
i = 0
for tag in p_tags:
    a_tag = tag.find("a")
    if a_tag is None:
        continue
    href = a_tag.get("href")
    if '_full_timetable' not in href: continue
    date = re.findall(r"[0-9][0-9][0-9][0-9][/-][0-9][0-9][/-][0-9][0-9]", tag.text)[0]
    date_obj = convert_date(date)

    href_basename = os.path.basename(href)
    datename = get_datename(href_basename)
    new_value = date_obj
    write_pdf = True
    if stored_dates:
        print("date: ", datename)
        print("stored dates: ", stored_dates)
        if datename not in stored_dates:
            stored_dates[datename] = "2020-01-01"
        old_value = convert_date(stored_dates[datename])
        write_pdf = new_value > old_value
        print(f"{new_value} vs. {old_value}")

    if (write_pdf):
        print(f"date is newer! Download them bad boys to {f'{DATADIR}/pdfs/{datename}.pdf'}.")
        response = request.urlopen(UWINPATH + href)
        with open(f"{DATADIR}/pdfs/{datename}.pdf", "wb") as fp:
            fp.write(response.read())
    else:
        print("date is the same")


    key = get_datename(href_basename)[:5]
    dates[key] = date_obj.strftime("%Y-%m-%d")
    print("{0} : {1}".format(date_obj, type(date_obj)))
    print("--------------")

if not stored_dates:
    with open(FILENAME, "w") as fp:
        json.dump(dates, fp, indent=4)
    print(f"dates: {dates}")

print("#########################################################################")
