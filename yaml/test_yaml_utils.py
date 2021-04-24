import unittest
from yaml_utils import read_yaml_from_file, write_yaml_to_file 

class TestYamlUtils(unittest.TestCase):
    def test_read_yaml_from_file(self):
        test_dict = read_yaml_from_file("test_read.yaml")
        print(test_dict)
    
    def test_write_yaml_to_file(self):
        test_dict = {
            "AERO-1970": {
                "name": " Prac: Prof Devt Pilot Training ",
                "type": "LEC",
                "sections": [
                    {
                        "number": "1",
                        "full?": False,
                        "credits": "3.00",
                        "days": "W",
                        "time": {
                            "start": "03:00 PM",
                            "end": "05:50 PM"
                        },
                        "room": " Face to Face-Talk to Dept ",
                        "prof": "Bacon,Tamsin A."
                    },
                    {
                        "number": "2",
                        "full?": False,
                        "credits": "3.00",
                        "days": "TH",
                        "time": {
                            "start": "03:00 PM",
                            "end": "05:50 PM"
                        },
                        "room": " Face to Face-Talk to Dept ",
                        "prof": "Bacon,Tamsin A."
                    }
                ]
            }
        }
        write_yaml_to_file(test_dict, "test_write.yaml")
