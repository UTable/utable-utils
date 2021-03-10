#!/usr/local/bin/python3.8

# python script that scrapes PDF data
# relies on script2.sh to generate the easy-to-parse almost-YAML file
# this code parses the rest of the code, and populates a django class

import subprocess
import re 
import sys 

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

debug = Debug(True)

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
        #         sub: [
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

        # reference  for easier accessing of the dictionary
        self.curr_section = self.res[self.curr_code]['sections'][self.curr_section_index]

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
            return code
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
            if 'sections' in self.res[self.curr_code]:
                self.init_section()
            debug.print(line)
            #sys.exit()
        
        debug.print("get other items")
        type_strlist = re.findall(REGEX_STRS["type"], line)
        if len(type_strlist) == 1:
            type_str = type_strlist[0]
            self.curr_section['type'] = type_str

        days_strlist = re.findall(REGEX_STRS["days"], line)
        if len(days_strlist) == 1:
            days = days_strlist[0]
            self.curr_section['days'] = days

        times_strlist = re.findall(REGEX_STRS["time"], line)
        if len(times_strlist) == 2:
            times = {}
            times["start"] = times_strlist[0]
            times["end"] = times_strlist[1]
            self.curr_section['times'] = times 

        prof_strlist = re.findall(REGEX_STRS["prof"], line)
        if len(days_strlist) > 0:
            self.curr_section['profs'] = prof_strlist 
        
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


class TTS:
    def __init__(self, *args, **kwargs):
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
                i += 1
                continue
            parser.parse(line)
            #if i == 10: break
            i += 1
        return parser.res
