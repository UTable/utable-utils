#!/bin/bash
# a simple awk command for stripping all the lines of a file. Useful for these empty line bloated text files. 
awk NF ../local-data/w2021.txt
