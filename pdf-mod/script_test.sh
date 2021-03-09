#!/bin/bash
#
# inputting script2, and formatting the Section portion
#
# starting to create the YAML results file. Still need to parse sections
# will do so in script3.sh

./script2.sh | gawk '
/^  Section/ {
	printf "  sections: [";
	split($0, a, /\b\(M|T|W|TH|F\)\+\b/, sep)
	for (i in a) {
		printf "(%s, %s), ", a[i], sep[i]
	}
	printf "]\n";
}  
1
' 

#done
# /^[A-Z][A-Z][A-Z][A-Z]-( )*[0-9][0-9X][0-9X][0-9X]/ {flag=0;split($0, a, "(-)", sep);print sep[0]}
