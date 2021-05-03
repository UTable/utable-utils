#!/usr/local/bin/python3.8

# Name: Bailey Chittle
# Date: Feb 3 2021
# Program Desc: simple program that takes a pdf and converts it to a text file, 
# used for processing and parsing text data. 
from tika import parser
import json

def pdf2txt(filename):
    raw = parser.from_file("../local-data/pdfs/"+filename)
    return raw["content"]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            print(pdf2txt(sys.argv[i]))
    else:
        print("usage: pdf2txt [filename.pdf]+")