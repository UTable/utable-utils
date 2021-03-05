# note: i would recommend redirecting stdout to a log file
from tika import parser
import re
import json
import sys


def scrape_timetable(filename):
    print("---------------")
    print(filename)
    print("---------------")
    # parses uses tika apache pdf bindings
    raw = parser.from_file("data/pdfs/"+filename+".pdf")

    raw = raw["content"]
    raw = raw[raw.index("Bldg/Room Professor")+len("Bldg/Room Professor"):]
    raw = raw.split("\n")
    i = 0
    for s in raw:
        # removes unnecessary pdf junk
        if s.find("Course Offerings") != -1:
            for j in range(11):
                #print(raw[i])
                raw.pop(i)
        i += 1

    courses_dict = {}
    i = 0    
    # organizes pdf using regex into json
    for s in raw:
        code = re.findall("[A-Z][A-Z][A-Z][A-Z]- *[0-9][0-9X][0-9X][0-9X]|$", s)[0]
        if code: # should almost always work
            j = i + 1
            while not re.findall("[A-Z][A-Z][A-Z][A-Z]-[0-9][0-9][0-9][0-9]|$", raw[j])[0]:
                s += " " + raw[j]
                j += 1
                if j >= len(raw): break
            iter = re.finditer(r"Section [0-9]+", s)
            indeces = [m.start(0) for m in iter]
            print("indeces: " + str(indeces))
            sections = []
            name = ""
            if indeces: 
                name = s[0:indeces[0]]
                for j in range(len(indeces)):
                    print(j)
                    start = indeces[j]
                    if j == len(indeces) - 1:
                        sections.append(s[start:])
                    else:
                        end = indeces[j + 1]
                        sections.append(s[start:end])
            else:
                iter = re.finditer(r"[^AP][MWTF]H? [0-9]", s)
                indeces = [m.start(0) for m in iter]
                print("new indeces: " + str(indeces))
                if indeces: 
                    name = s[0:indeces[0]]
                    for j in range(len(indeces)):
                        start = indeces[j]
                        if j == len(indeces) - 1:
                            sections.append(s[start:])
                        else:
                            end = indeces[j + 1]
                            sections.append(s[start:end])
            name = name[name.find("(-)") + len("(-)"):]
            course_dict = {}
            print(code)
            print(sections)            
            course_dict["name"] = name
            course_dict["type"] = "LAB" if sections[0].find("LEC") == -1 else "LEC"
            course_dict["sections"] = []
            j = 0
            for section in sections:
                section_dict = {}
                if section.find("Section") == -1:
                    section_dict["number"] = None
                else:
                    section_dict["number"] = re.findall(r"[0-9]+", section)[0]
                if section.find(" Full ") == -1:
                    section_dict["full?"] = False
                else:
                    section_dict["full?"] = True
                credits = re.search(r"[0-9]\.00", section)
                if credits:
                    section_dict["credits"] = credits.group(0)
                days = re.search(r"[^AP][MWTF]+H? [0-9]", section)
                if days:
                    days = days.group(0)
                    days = days[1:-2]
                    section_dict["days"] = days
                time = re.findall(r"[01][0-9]:[0-9][0-9] [AP]M", section)
                time_dict = {}
                if time:
                    time_dict["start"] = time[0]
                    time_dict["end"] = time[1]
                section_dict["time"] = time_dict
                indices = re.finditer(r"[01][0-9]:[0-9][0-9] [AP]M", section)
                index1 = []
                for m in indices:
                    if m:
                        index1.append(m.start(0))
                if len(index1) > 1:
                    index1 = index1[1] + len(time[1])
                    index2 = re.search(r"[A-Z][a-zA-Z]*,[A-Z][a-zA-Z]* ?[A-Z]?\.?", section)
                    if index2:
                        index2 = index2.start(0)
                        section_dict["room"] = section[index1:index2]
                prof = None
                re_profs = re.findall(r"[A-Z][a-zA-Z]*,[A-Z][a-zA-Z]* ?[A-Z]?\.?", section)
                if re_profs:
                    prof = re_profs[0]
                    section_dict["prof"] = prof
                j += 1
                course_dict["sections"].append(section_dict)
            print(course_dict)
            if code in courses_dict:
                print("test")
                j = 1
                while code + "-" + str(j) in courses_dict:
                    j += 1
                courses_dict[code + "-" + str(j)] = course_dict
            else:
                courses_dict[code] = course_dict
        i += 1

    fp = open("data/pdfs/"+filename+".txt", "w")
    fp.write("\n".join(raw))
    fp.close()

    fp = open("data/"+filename+".json", "w")
    json.dump(courses_dict, fp, indent=4)
    fp.close()

    fp = open("data/api.txt", "a")
    fp.write(filename)
    fp.close()

# allows arguments except for 1st argument (which is just what program is running...)
ARGS = sys.argv[1:]
# if no arguments given, run default file
DEFAULT_FILENAME = "f2019"

if ARGS:
    for arg in ARGS:
        scrape_timetable(arg)
else:
    scrape_timetable(DEFAULT_FILENAME)