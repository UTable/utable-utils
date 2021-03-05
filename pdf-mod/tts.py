#!/usr/local/bin/python3.8

# python script that scrapes PDF data
# relies on script2.sh to generate the easy-to-parse almost-YAML file
# this code parses the rest of the code, and populates a django class

import subprocess
import re 

REGEX_STRS = {
    "section": r"^  Section",
    "days": r"\b(M|T|W|TH|F)+\b",
    "type": r"(LEC|LAB)",
    "time": r"[0-9][0-9] [AP]M",
    "prof": r"[a-zA-Z]+,[a-zA-Z\.]+",
}

class TTS:
    def __init__(self):
        self.get_res(["./script2.sh"])

    # gets the result of a separate script/executable, so it can be parsed with python
    # saves in the state at exec_res
    def get_res(self, execution):
        self.exec_res = subprocess.run(
            execution, capture_output=True, text=True
        )
        return self.exec_res

    # gets the result of the executed function in get_res as a dict. 
    # Assumes that get_res is run (it should run in the constructor)
    # saves the results as a dictionary object called res.
    def get_dict(self):
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
        res = {}
        for x in self.exec_res.stdout.split("\n"):
            section_match = re.search(REGEX_STRS["section"], x)
            if section_match:
                section_str = section_match.group(0)
                if section_str not in res:
                    res[section_str] = {}

                # NOTE: this might cause issues in the future
                # dates are optional, so there must be a way to split data on a required value
                #
                # this should be fine because subsections exist to differentiate time only, 
                #   at least from what I've seen.
                #
                # also subsections with one with a date and one without a date is not allowed
                # but this most likely also doesn't exist, as a section without a date would not be in a separate subsection
                days_strlist = re.findall(REGEX_STRS["days"], x)
                subsec_strlist = re.split(REGEX_STRS["type"], x)
                type_match = re.search(REGEX_STRS["type"], x)
                if not days_strlist:
                    span = type_match.span()
                    subsec_strlist = [x[:span[1]], "", x[span[1]:]]
                    #print(x)
                # print(x)
                # section info
                print(subsec_strlist[0])
                for i in range(int(len(subsec_strlist) / 2)):
                    # date
                    # other data
                    #print(subsec_strlist[i * 2 + 2])
                    break 
                continue
            #print(x)
        return res
