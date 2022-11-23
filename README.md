# utable-utils
Utility functions for UTable running on the production server

### Now open-source!
Since production is now offline (there is nothing to hack), I figured I would open-source the pdf utilities if future students want to parse uwindsor timetable data 
(as of now they still use the same method of showing course info via pdfs in the same format as they have since I started)

key files:
- tts_cronjob.py         // text-to-scrape cronjob utility. this used to scrape timetable data on an automated basis
- web-fetch/checkdate.py // checks dates and downloads necessary pdf data
- pdf-mod/pdf2txt.py     // does what you think
- pdf-mod/tts.py         // scrapes the text and sends to appropriate storage facilities (database, json files, etc.) (also has a command line interface)
