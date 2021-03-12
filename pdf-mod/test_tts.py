import unittest
from tts import TTS
import json

class TestTTS(unittest.TestCase):
    def test_init(self):
        tts = TTS()
    def test_get_res(self):
        tts = TTS()
        len_exec = 197283 
        if len_exec != len(tts.exec_res.stdout):
            raise Exception(f"lengths do not match! {len_exec} != {len(tts.exec_res.stdout)}")

    def test_set_db(self):
        #tts = TTS(textfile="test/test2.txt", debug=True)
        #tts = TTS(debug=True, amt=5)
        tts = TTS(debug=False)
        res = tts.get_dict()
        with open("../local-data/w2021.json", "w") as fp:
            json.dump(res, fp, indent=4)
        #print(res)
        print("saving to test database...")
        tts.set_db(res)