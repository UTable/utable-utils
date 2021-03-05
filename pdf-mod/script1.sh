#!/bin/bash
# gets course code and course name, separated by (-)
# TODO: change w2021.txt to use any txt file. 
for var in "$@"
do
	#STR="{print $var}"
	# echo $STR
	awk -F "\\\(-\\\) " "/\(-\)/ {print $var}" ../local-data/w2021.txt 
done
