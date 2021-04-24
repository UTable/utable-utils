import unittest
from tts import TTS

class TestTTS(unittest.TestCase):
    def test_init(self):
        tts = TTS()
    def test_get_res(self):
        tts = TTS()
        len_exec = 195821
        if len_exec != len(tts.exec_res.stdout):
            raise Exception(f"lengths do not match! {len_exec} != {len(tts.exec_res.stdout)}")

    def test_get_dict(self):
        tts = TTS()
        res = tts.get_dict()
        print(res)
