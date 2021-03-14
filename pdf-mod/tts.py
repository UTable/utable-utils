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
    "days": r"\b(M|T|W|TH|F)+\b",
    "type": r"(LEC|LAB)",
    "time": r"[0-9][0-9]:[0-9][0-9] [AP]M",
    "prof": r"[a-zA-Z]+,[a-zA-Z\.]+",
    "name": r'"[^"]*"'
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
    'subsection': 3,
}

QUERIES = {
    'semester': """
INSERT INTO public.utable_semester
("courseName", "courseCode")
VALUES('%s','%s');
""",
    'course': """

""",

    'section': """

""",

    'subsection': """

""",

}
# saves the dictionary stored in memory into the database conenction
import psycopg2

class DictToDB:
    def __init__(self, dic):
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
    
    def populate(self, key, **kwargs):
        if key == TABLES['semester']:
            pass
            #db.cur.execute(QUERIES['semester'], (kwargs['date']))
        elif key == TABLES['course']:
            pass
            #db.cur.execute(QUERIES['course'], (kwargs['code'], kwargs['name']))
        elif key == TABLES['section']:
            pass
            #db.cur.execute(QUERIES['section'], (kwargs['num'], kwargs['type_']))
        elif key == TABLES['subsection']:
            pass
            #db.cur.execute(QUERIES['subsection'], (kwargs['days'], kwargs['start_time'], kwargs['end_time']))
        else:
            raise Exception(f"invalid key given to db.populate: {key}. Try picking a key from TABLES variable.")
        



class TTS:
    def __init__(self, *args, **kwargs):
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
        db = DictToDB(dic)
        # w2021
        db.populate(TABLES['semester'], date=self.semester_date)

        # iterating through dictionary in memory, writing to database
        for code in dic:
            if len(code) > 10:
                print(code, "has length > 10")
            content = dic[code]
            name = content['name']
            sections = content['sections']
            db.populate(TABLES['course'], code=code, name=name)

            for section in sections:
                num=None
                type_=None
                if 'num' in section:
                    num = section['num']
                if 'type' in section:
                    type_ = section['type']
                db.populate(TABLES['section'], num=num, type_=type_)
                subsections = section['subsections']
                for subsec in subsections:
                    days=None
                    start_time=None
                    end_time=None
                    if 'days' in subsec:
                        days = subsec['days']
                    if 'time' in subsec:
                        time = subsec['times']
                        start_time = datetime.strptime(time['start'], "%I:%M %p").time()
                        end_time = datetime.strptime(time['end'], "%I:%M %p").time()
                    if 'profs' in subsec:
                        profs = subsec['profs']
                    db.populate(
                        TABLES['subsection'], 
                        days=days,
                        start_time=start_time,
                        end_time=end_time,
                    )
        #db.commit()