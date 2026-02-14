
import unittest
import sys
from pathlib import Path

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.transform.parser import LanguageParser

class TestExclusionParsing(unittest.TestCase):
    def setUp(self):
        self.parser = LanguageParser()

    def test_single_exclusion(self):
        # "ITP 제외"
        note = "ITP 제외"
        result = self.parser.parse_exclusions(note)
        self.assertIn("TOEFL_ITP", result)

        # "TOEIC 제외"
        note = "TOEIC 제외"
        result = self.parser.parse_exclusions(note)
        self.assertIn("TOEIC", result)

    def test_comma_separated(self):
        # "TOEIC, ITP 제외"
        note = "TOEIC, ITP 제외"
        result = self.parser.parse_exclusions(note)
        self.assertIn("TOEIC", result)
        self.assertIn("TOEFL_ITP", result)

    def test_slash_separated(self):
        # "TOEIC/TOEFL ITP 제외"
        # Note: "TOEFL ITP" usually parses as "TOEFL_ITP"
        note = "TOEIC/TOEFL ITP 제외"
        result = self.parser.parse_exclusions(note)
        print(f"DEBUG: {note} -> {result}")
        self.assertIn("TOEIC", result)
        self.assertIn("TOEFL_ITP", result)

    def test_impossible_keyword(self):
        # "* TOEIC 불가"
        note = "* TOEIC 불가"
        result = self.parser.parse_exclusions(note)
        self.assertIn("TOEIC", result)

    def test_parentheses(self):
        # "* TOEFL만 인정(IELTS, TOEIC 제외)"
        note = "* TOEFL만 인정(IELTS, TOEIC 제외)"
        result = self.parser.parse_exclusions(note)
        self.assertIn("IELTS", result)
        self.assertIn("TOEIC", result)

    def test_complex_newlines(self):
        # * ITP 제외 \n * TOEIC 제외
        note = "* ITP 제외 \n * TOEIC 제외"
        result = self.parser.parse_exclusions(note)
        self.assertIn("TOEFL_ITP", result)
        self.assertIn("TOEIC", result)

    def test_no_exclusion(self):
        note = "No exclusion here"
        result = self.parser.parse_exclusions(note)
        self.assertEqual(result, [])

    def test_invalid_exam(self):
        # "TOEFL Home Edition 제외" - "TOEFL Home Edition" is not in known exams
        # Ideally it should be ignored or maybe just "TOEFL" if it extracts that far?
        # My implementation looks for KNOWN exams. "Home Edition" is not known. "TOEFL" is.
        # So "TOEFL Home Edition 제외" might match "TOEFL" if my logic is loose, or nothing if strict.
        # Let's see what happens.
        note = "TOEFL Home Edition 제외"
        result = self.parser.parse_exclusions(note)
        # If it picks up TOEFL, that might be wrong if Home Edition is a specific Type.
        # But if the user says "TOEFL Home Ed 제외", they mean TOEFL Home Ed is invalid.
        # If we optimize for "known exams", "TOEFL" is known.
        # If it returns "TOEFL", it means TOEFL is excluded. That might be too aggressive if they accept "TOEFL IBT".
        # But usually "TOEFL 제외" means all TOEFL.
        # Let's check what it does.
        pass

if __name__ == "__main__":
    unittest.main()
