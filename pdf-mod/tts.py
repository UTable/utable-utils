#!/usr/local/bin/python3.8

# python script that scrapes PDF data
# relies on script2.sh to generate the easy-to-parse almost-YAML file
# this code parses the rest of the code, and populates a django class

import subprocess
import re 
import sys 

from datetime import datetime

REGEX_STRS = {
    "code": r"^[A-Z][A-Z][A-Z][A-Z]-( )*[0-9][0-9X][0-9X][0-9X]",
    "section": r"^  Section [0-9]+",
    "days": r"\b(M|T|W|TH|F|SA|SU)+\b",
    "type": r"(LEC|LAB)",
    "time": r"[0-9][0-9]:[0-9][0-9] [AP]M",
    "prof": r"[a-zA-Z\-]+,[a-zA-Z\.\-]+",
    "name": r'"[^"]*"',
    "full": r'Full'
}

class Debug:
    def __init__(self, debug):
        self.DEBUG = debug

    def print(self, *args):
        if self.DEBUG:
            for arg in args:
                print(arg, end=' ')
            print()

#debug = Debug(False)
debug = None

# converts the pdf in text format to a dictionary
class TextToDictParser:
    def __init__(self):
        # res should containe an object in the following form:
        #
        # w2021 {
        #   "STAT-2910": {
        #     name: "Statistics for the sciences",
        #     sections: [
        #       {
        #         num: 1,
        #         credits: 1,
        #         type: LEC,
        #         subsections: [
        #           {
        #             Dates: ...,
        #             start_time: 08:30 AM,
        #             end_time: 09:50 AM,
        #             location: online,
        #             prof(s): Myron Hlynka
        #           }
        #         ]
        #       }
        #     ]
        #   }
        # }
        #
        self.res = {}

        # tts is in various states, before repeating from the beginning once the state is complete
        self.states = {
            "code": 0,
            "name": 1,
            "section": 2,
        }
        self.curr_state = self.states["code"]   # self-managed state
        self.curr_code = None                   # the current course code (in res) to add information to
        self.curr_section_index = -1             # NOT section number, rather, the index in the section array

        self.curr_section = None

    
    # variable initializations specific to sections. 
    # relies on curr_code existing
    def init_section(self):
        if 'sections' not in self.res[self.curr_code]:
            self.res[self.curr_code]['sections'] = []
            self.curr_section_index = -1

        self.curr_section_index += 1

        # append a new dictionary for section
        self.res[self.curr_code]['sections'].append({})

        # reference for easier accessing of the dictionary
        self.curr_section = self.res[self.curr_code]['sections'][self.curr_section_index]
    
    def init_subsection(self):
        if 'subsections' not in self.curr_section:
            self.curr_section['subsections'] = []
            self.curr_subsection_index = -1
        self.curr_subsection_index += 1

        # append a new dictionary for sub-section
        self.curr_section['subsections'].append({})

        # reference for easier accessing of the dictionary
        self.curr_subsection = self.curr_section['subsections'][self.curr_subsection_index]

    # parses line by line, updating state when need be to reflect parse mode
    def parse(self, line):
        if self.curr_state == self.states["code"]:
            code = self.parse_code(line)
            if code: 
                inc = 0
                while code in self.res:
                    code += f"[{inc}]"
                self.res[code] = {}
                self.curr_code = code
        elif self.curr_state == self.states["name"]:
            if self.curr_code:
                name = self.parse_name(line)
                if name:
                    debug.print("name:", name)
                    name = name[1:-1].strip()
                    self.res[self.curr_code]["name"] = name
        elif self.curr_state == self.states["section"]:
            # stateful section parsing done within this section
            self.parse_sections(line)
    
    # parse_code parses a code out of the line and returns it
    def parse_code(self, line):
        code_match = re.search(REGEX_STRS['code'], line)
        if code_match:
            self.curr_state = self.states['name']
            code = code_match.group()
            debug.print("code:", code)
            return code.replace(" ", "")
        return None

    def parse_name(self, line):
        name_match = re.search(REGEX_STRS['name'], line)
        if name_match:
            self.curr_state = self.states['section']
            name = name_match.group()
            return name 
        return None
        
    # parse_sections: parses (potentially) multiple sections
    def parse_sections(self, line):
        # if section number is available, use it as a section number in section array
        section = self.parse_section(line)
        if section:
            debug.print("is a new section in section array")
            self.init_section()
            self.init_subsection()

            # get number of section
            num_match = re.search(r"[0-9]+", line)
            if num_match:
                num = num_match.group()
                self.add_to_section("num", num)
        else:
            # do something with unnamed section
            debug.print("line has no section!")
            code_check = re.search(REGEX_STRS["code"], line)
            if code_check:
                debug.print("is a new course code")
                self.curr_state = self.states['code']
                self.parse(line)
                return
            if 'sections' not in self.res[self.curr_code]:
                self.init_section()
            self.init_subsection()
            debug.print(line)
            #sys.exit()
        
        debug.print("get other items")

        type_strlist = re.findall(REGEX_STRS["full"], line)
        self.curr_section['full?'] = True if len(type_strlist) != 0 else False

        type_strlist = re.findall(REGEX_STRS["type"], line)
        if len(type_strlist) == 1:
            type_str = type_strlist[0]
            self.curr_section['type'] = type_str

        days_match = re.search(REGEX_STRS["days"], line)
        if days_match:
            self.curr_subsection['days'] = days_match.group() 

        times_strlist = re.findall(REGEX_STRS["time"], line)
        if len(times_strlist) == 2:
            times = {}
            times["start"] = times_strlist[0]
            times["end"] = times_strlist[1]
            self.curr_subsection['times'] = times 

        prof_strlist = re.findall(REGEX_STRS["prof"], line)
        if len(prof_strlist) > 0:
            self.curr_subsection['profs'] = prof_strlist 
        
    # add_to_section: magic function that adds specific items to sections. 
    #   analyzes state and acts accordingly
    #   give it a key and val and it will do the rest
    def add_to_section(self, key, val):
        if key == "num":
            debug.print(f"{key}: {val}")
            self.curr_section[key] = val 


    def parse_section(self, line):
        section_match = re.search(REGEX_STRS['section'], line)
        if section_match:
            section = section_match.group()
            return section 
        return None

# list of databases to make a possible connection to
DBs = {
    'psql': 0,
}

TABLES = {
    'semester': 0,
    'course': 1,
    'section': 2,
    'subsec': 3,
    'prof': 4,
    'subsec_prof': 5,
}

COURSE_QUERY = {
    'insert': """
INSERT INTO public.utable_course
("courseName", "courseCode")
VALUES(%s, %s)
RETURNING id;""",
    'select': """
SELECT id, "courseName", "courseCode"
FROM public.utable_course
WHERE "courseName" = %s
AND "courseCode" = %s;"""
}

PROF_QUERY = {
        'insert': """
INSERT INTO public.utable_professor
("firstName", "lastName")
VALUES(%s, %s)
RETURNING id;""",
        'select': """
SELECT id, "firstName", "lastName"
FROM public.utable_professor
WHERE "firstName" = %s
AND "lastName" = %s;"""
}

SECTION_QUERY = {
        'insert': """
INSERT INTO public.utable_section
("sectionNum", "sectionType", course_id, semester_id)
VALUES(%s, %s, %s, %s)
RETURNING id;""",
        'select': """
SELECT id, "sectionNum", "sectionType", course_id, semester_id
FROM public.utable_section;
WHERE utable_section.sectionNum = %s
AND utable_section.sectionType = %s
AND utable_section.course_id = %s
AND utable_section.semester_id = %s""",
}

SEMESTER_QUERY = {
    'insert': """
INSERT INTO public.utable_semester
("semesterSeason", "date")
VALUES(%s, %s)
RETURNING id;""",
    'select': """
SELECT id, "semesterSeason", "date"
FROM public.utable_semester
WHERE "semesterSeaoson"=%s
AND "date"=%s;"""
}

SUBSECTION_QUERY = {
    'insert': """
INSERT INTO public.utable_subsection
("day", "startTime", "endTime", "location", section_id)
VALUES(%s, %s, %s, %s, %s)
RETURNING id;""",
    'select': """
SELECT id, "day", "startTime", "endTime", "location", section_id
FROM public.utable_subsection
WHERE utable_subsection.day = %s
AND utable_subsection.startTime = %s
AND utable_subsection.endTime = %s
AND utable_subsection.location = %s
AND utable_subsection.section_id = %s
;"""
}

SUBSEC_PROF_QUERY = {
    'insert': """
INSERT INTO public.utable_subsection_professors
(subsection_id, professor_id)
VALUES(%s, %s)
RETURNING id;""",
}

# saves the dictionary stored in memory into the database conenction
import psycopg2

class DictToDB:
    def __init__(self):
        self.make_connection(DBs['psql'])
    
    def __del__(self):
        self.conn.close()
    
    def commit(self):
        self.conn.commit()
    
    def make_connection(self, db_id):
        if db_id == DBs['psql']:
            self.conn = psycopg2.connect(
                dbname='utable_beta', 
                host='localhost', 
                port='5432', 
                user='utable_auth', 
                password='5Nu5j8GXI2j9'
            )
    
            self.cur = self.conn.cursor()
    
    def execute(self, query, key, kwargs):
        try:
            if key == TABLES['semester']:
                if kwargs['date'] and len(kwargs['date']) == 5:
                    #self.cur.execute(SEMESTER_QUERY, (kwargs['date'][0], kwargs['date'][1:]))
                    self.cur.execute(SEMESTER_QUERY[query], (kwargs['date'][0], kwargs['date'][1:]))
                else:
                    self.cur.execute(SEMESTER_QUERY[query], (None, None))
            elif key == TABLES['prof']:
                self.cur.execute(PROF_QUERY[query], (kwargs['first_name'], kwargs['last_name']))
            elif key == TABLES['course']:
                self.cur.execute(COURSE_QUERY[query], (kwargs['name'], kwargs['code']))
            elif key == TABLES['section']:
                self.cur.execute(SECTION_QUERY[query], (kwargs['num'], kwargs['type_'], kwargs['course_id'], kwargs['semester_id']))
            elif key == TABLES['subsec']:
                days = kwargs['days']
                if days is None:
                    days = ''
                self.cur.execute(SUBSECTION_QUERY[query], (days, kwargs['start_time'], kwargs['end_time'], kwargs['location'], kwargs['section_id']))
            elif key == TABLES['subsec_prof']:
                self.cur.execute(SUBSEC_PROF_QUERY[query], (kwargs['subsec_id'], kwargs['prof_id']))
            else:
                raise Exception(f"invalid key given to db.populate: {key}. Try picking a key from TABLES variable.")
            if query == "insert":
                # get the id
                res = self.cur.fetchone()[0]
            elif query == "select":
                # get all of the select statements
                res = self.cur.fetchall()
            return res
        except Exception as e:
            print(f"error at {key} with arguments {kwargs}")
            raise e

    def select(self, key, **kwargs):
        return self.execute('select', key, kwargs)
    def populate(self, key, **kwargs):
        return self.execute('insert', key, kwargs)
   
    def delete_all_rows(self):
        query = """
        TRUNCATE utable_course,
        utable_professor,
        utable_section,
        utable_section_students,
        utable_student,
        utable_semester,
        utable_subsection,
        utable_subsection_professors
        RESTART IDENTITY;
        """
        self.cur.execute(query)
        self.commit()
        
class TTS:
    def __init__(self, *args, **kwargs):
        self.db = DictToDB()
        global debug
        if 'debug' in kwargs:
            debug = Debug(kwargs['debug'])
        else:
            debug = Debug(False)
        
        if 'amt' in kwargs:
            self.amt = kwargs['amt']
        else:
            self.amt = None

        if 'exec' in kwargs:
            self.get_res([kwargs['exec']])
        elif 'textfile' in kwargs:
            with open(kwargs['textfile'], "r") as fp:
                self.res_str = fp.read()
        else:
            self.get_res(["./script2.sh"])

    # gets the result of a separate script/executable, so it can be parsed with python
    # saves in the state at exec_res
    def get_res(self, execution):
        print(f"execution: {execution}")
        self.exec_res = subprocess.run(
            execution, capture_output=True, text=True
        )
        self.res_str = self.exec_res.stdout
        return self.exec_res

    # gets the result of the executed function in get_res as a dict. 
    # Assumes that get_res is run (it should run in the constructor)
    # saves the results as a dictionary object called res.
    def get_dict(self):
        lines = self.res_str.split("\n")
        parser = TextToDictParser()
        i = 0
        for line in lines:
            # skip the first empty line
            debug.print(f"{i}: {line}")
            if i == 0:
                self.semester_date = line
                i += 1
                continue
            parser.parse(line)
            if self.amt:
                if i == self.amt: break
            i += 1
        return parser.res

    # sets the current data stored in res_dict into the database connection that is set up
    def set_db(self, dic):
        db = self.db
        db.delete_all_rows()
        db.commit()
        # w2021
        semester_id = db.populate(TABLES['semester'], date=self.semester_date)

        # iterating through dictionary in memory, writing to database
        try:
            for code in dic:
                content = dic[code]
                if "[" in code and "]" in code:
                    i = code.find("[")
                    code = code[:i]
                name = content['name']
                sections = content['sections']
                course_id = db.populate(TABLES['course'], code=code, name=name)

                tba_id = None

                for section in sections:
                    num=None
                    type_=None
                    if 'num' in section:
                        num = section['num']
                    if 'type' in section:
                        type_ = section['type']
                    section_id = db.populate(TABLES['section'], num=num, type_=type_, course_id=course_id, semester_id=semester_id)
                    subsections = section['subsections']
                    for subsec in subsections:
                        print(f"subsec: {subsec}")
                        days=None
                        start_time=None
                        end_time=None
                        first_name=None
                        last_name=None

                        prof_id=None
                        subsec_id=None
                        location="Online"
                        if 'days' in subsec:
                            days = subsec['days']
                        if 'times' in subsec:
                            time = subsec['times']
                            start_time = datetime.strptime(time['start'], "%I:%M %p").time()
                            end_time = datetime.strptime(time['end'], "%I:%M %p").time()
                        if 'profs' in subsec:
                            profs = subsec['profs']
                            prof_ids = []
                            for prof in profs:
                                if ',' in prof:
                                    prof = prof.split(',')
                                    first_name = prof[1]
                                    last_name = prof[0]
                                    prof_data = db.select(TABLES['prof'],first_name=first_name, last_name=last_name)
                                    if prof_data:
                                        prof_id = prof_data[0][0]
                                    else:
                                        prof_id = None
                                    if prof_id is None:
                                        print(f"new prof! {first_name},{last_name}")
                                        prof_id = db.populate(TABLES['prof'],first_name=first_name, last_name=last_name)
                                    else:
                                        print(f"old prof: {prof_id}")
                                    prof_ids.append(prof_id)
                        subsec_id = db.populate(TABLES['subsec'],days=days,start_time=start_time,end_time=end_time, location=location, section_id=section_id)
                        if prof_ids and subsec_id is not None:
                            for prof_id in prof_ids:
                                db.populate(TABLES['subsec_prof'], subsec_id=subsec_id, prof_id=prof_id)
            db.commit()
        except Exception as e:
            db.commit()
            raise e


if __name__ == "__main__":
    tts = TTS(debug=False)
    print("The Text To Storage program")
    print("what would you like to do?")
    print("")
    print("------------------------------------")
    print("get dict/gd: get the dictionary object of the course")
    print("set db/sd: sets the database based on the json")
    print("dump json/dj: dumps dictionary in memory to json") 
    print("commit/c: commit any changes you made to the database")
    print("quit/q: quit the program")
    print("------------------------------------")

    dic = None
    while True:
        option = input("> ")
        if option == "c" or option == "commit":
            print("committing to database")
            tts.db.commit()
        elif option == "gd" or option == "get dict":
            print("getting dictionary...")
            dic = tts.get_dict()
        elif option == "sd" or option == "set db":
            print("setting database...")
            if dic is None:
                print("don't have a dictionary to parse to database yet...")
                continue
            tts.set_db(dic)
        elif option == "dj" or option == "dump json":
            print("dumping json...")
            import json
            with open("../local-data/w2021.json", "w") as fp:
                json.dump(dic, fp, indent=4)
        elif option == 'q' or option == 'quit':
            print("bye!")
            break
        else:
            print("invalid command, please try again!")

