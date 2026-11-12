import json
from pathlib import Path
import unittest
from scripts.tests.test_storyboard import ctx
from scripts.validation.storyboard import validate

class TestValidationContract(unittest.TestCase):
    def test_pre_refactor_results(self):
        cases=json.loads((Path(__file__).parent/'fixtures'/'storyboard-validation.json').read_text())
        for case in cases:
            with self.subTest(storyboard=case['storyboard']):
                self.assertEqual(list(validate(case['storyboard'],ctx())),case['expected'])
