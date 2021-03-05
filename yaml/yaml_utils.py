#!/usr/local/bin/python3.8

import yaml

#filename: string of a relative (or absolute) filename path to write to. 
def read_yaml_from_file(filename):
    with open(filename, "r") as fp:
        yaml_data = yaml.safe_load(fp)
        return yaml_data

# yaml_data: a python object that is going to be converted to a YAML file
# filename: string of a relative (or absolute) filename path to write to. 
def write_yaml_to_file(yaml_data, filename):
    with open(filename, "w") as fp:
        yaml.dump(yaml_data, fp)
        # yaml.dump(yaml_data, fp, default_flow_style=False, allow_unicode=True)