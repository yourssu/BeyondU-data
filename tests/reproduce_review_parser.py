import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.transform.parser import ReviewParser

def test_review_parser():
    parser = ReviewParser()
    test_cases = [
        ("Y(2018)", (True, "2018")),
        ("Y(2013-2019)", (True, "2013-2019")),
        ("X", (False, None)),
        (None, (False, None)),
        ("", (False, None)),
        # Potential edge cases that might be causing the failure
        ("Y (2023)", (True, "2023")),  # Space
        ("y(2023)", (True, "2023")),   # Lowercase
        ("YES", (True, None)),         # Now valid
        ("2023", (True, "2023")),      # Now valid
        ("O", (True, None)),           # Now valid
    ]

    print("Testing ReviewParser...")
    failures = 0
    for input_text, expected in test_cases:
        result = parser.parse(input_text)
        if result != expected:
            print(f"FAIL: Input '{input_text}' -> Expected {expected}, Got {result}")
            failures += 1
        else:
            print(f"PASS: Input '{input_text}' -> {result}")

    if failures == 0:
        print("\nAll tests passed!")
    else:
        print(f"\n{failures} tests failed.")

if __name__ == "__main__":
    test_review_parser()
