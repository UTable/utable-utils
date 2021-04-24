#!/bin/bash
#
# Pretty formatting of the ugly PDF parse by tika
# gets all the information I need:
# - course code
# - course name
#
# starting to create the YAML results file. Still need to parse sections
# will do so in script3.sh

./strip_empty_lines.sh | gawk '
	BEGIN {printf "w2021";flag=0} 
	/^(Section|(M|T|W|TH|F|SA|SU)+ )/ {flag=1;printf "\n  "}  
	/^[A-Z][A-Z][A-Z][A-Z]-( )*[0-9][0-9X][0-9X][0-9X]/ {
		flag=0;
		split($0, a, "\\\(-\\\)", sep);
		printf "\n%s\n  name: \"%s\"", a[1], a[2]
	}
	/Winter 2021 Course Offerings/ {flag=0}
	flag {printf "%s ", $0}
' 

#done
# /^[A-Z][A-Z][A-Z][A-Z]-( )*[0-9][0-9X][0-9X][0-9X]/ {flag=0;split($0, a, "(-)", sep);print sep[0]}
