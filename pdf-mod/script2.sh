#!/bin/bash
#
# Pretty formatting of the ugly PDF parse by tika
# still needs more parsing in tts.py

./strip_empty_lines.sh $1 | gawk '
	BEGIN {printf "w2021";flag=0} 
	/^(Section|(M|T|W|TH|F|SA|SU)+ )/ {flag=1;printf "\n  "}  
	/^[A-Z][A-Z][A-Z][A-Z]-( )*[0-9][0-9X][0-9X][0-9X]/ {
		flag=0;
		split($0, a, "\\\(-\\\)", sep);
		printf "\n%s\n  name: \"%s\"", a[1], a[2]
	}
	/Course Offerings/ {flag=0}
	flag {printf "%s ", $0}
' 

#done
# /^[A-Z][A-Z][A-Z][A-Z]-( )*[0-9][0-9X][0-9X][0-9X]/ {flag=0;split($0, a, "(-)", sep);print sep[0]}
