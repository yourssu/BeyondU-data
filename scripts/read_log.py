import sys
from pathlib import Path

def print_log():
    keywords = ["Extracted", "Cleaned", "Loaded", "ERROR", "WARNING", "Total", "ReviewParser"]
    try:
        with open("etl.log", "r", encoding="utf-16le") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if any(k in line for k in keywords):
                    print(line.strip())
                    if "ERROR" in line:
                         for j in range(1, 25):
                             if i + j < len(lines):
                                 print(f"  CTX: {lines[i+j].strip()}")
    except UnicodeError:
        try:
             with open("etl.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if any(k in line for k in keywords):
                        print(line.strip())
                        if "ERROR" in line:
                            for j in range(1, 25):
                                if i + j < len(lines):
                                    print(f"  CTX: {lines[i+j].strip()}")
        except Exception as e:
            print(f"Error with utf-8: {e}")
    except Exception as e:
        print(f"Error reading log: {e}")

if __name__ == "__main__":
    print_log()
