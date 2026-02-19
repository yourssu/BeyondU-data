import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extract.excel_reader import ExcelReader
from src.config import settings
import pandas as pd
import re

def analyze_headers():
    data_dir = settings.raw_data_dir
    files = sorted(list(data_dir.glob("*.xlsx")))
    
    unique_headers = set()
    header_mapping = {} # Header -> count
    
    print(f"Scanning {len(files)} files...")
    
    for file_path in files:
        if file_path.name.startswith("~"): continue
        try:
            # We need to peek at raw headers before mapping
            # But ExcelReader maps them inside read().
            # Let's use openpyxl directly or modify ExcelReader to show raw headers.
            # actually logic in ExcelReader:
            # headers = [str(x).strip() if x else f"Unnamed_{i}" for i, x in enumerate(data[header_idx])]
            
            # Let's instantiate Reader and use its _find_header_row logic if possible, 
            # or just read and see what's unmapped (original names are lost).
            
            # Better: Write a mini-reader here to see RAW headers
            from openpyxl import load_workbook
            wb = load_workbook(file_path, data_only=True)
            sheet = wb.active
            data = []
            for row in sheet.rows:
                data.append([cell.value for cell in row])
            
            # Find header row (same logic as Reader)
            keywords = ["파견국가", "국가", "대학명"]
            if header_idx != -1:
                headers = [str(x).strip() if x else f"Unnamed_{i}" for i, x in enumerate(data[header_idx])]
                print(f"\n[{file_path.name}]")
                print(f"Headers: {headers}")
                
                # Check next row for sub-headers
                if header_idx + 1 < len(data):
                    next_row = [str(x).strip() if x else "None" for x in data[header_idx+1]]
                    print(f"Next Row: {next_row}")
                
                # Regex Check
                match = re.search(r"(\d{4})[-_](\d|여름|겨울).*?학기", file_path.name)
                print(f"Regex match: {match.groups() if match else 'NO MATCH'}")
                
            else:
                print(f"\n[{file_path.name}] Header row not found with keywords {keywords}")
                
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

if __name__ == "__main__":
    analyze_headers()
