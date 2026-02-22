import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.extract.excel_reader import ExcelReader
from src.transform.cleaner import DataCleaner
from src.transform.parser import GPAParser

def main():
    file_path = Path('data/raw/2026-2 교환학생 파견가능대학 및 지원자격(1차).xlsx')
    reader = ExcelReader(file_path)
    df = reader.read()
    
    cleaner = DataCleaner(df)
    df_clean = cleaner.clean()
    
    gpa_parser = GPAParser()
    
    print("--- Checking Shandong Normal University ---")
    idx = df['name_eng'].str.contains('Shandong Normal', na=False, case=False)
    for _, row in df[idx].iterrows():
        print("RAW Excel Reader Output:")
        print(f"  name_eng: {row.get('name_eng')}")
        print(f"  min_gpa (Raw): '{row.get('min_gpa')}'")
        print(f"  All headers matched: {list(row.keys())}")
        
    for _, row in df_clean[idx].iterrows():
        print("\nCleaned Output:")
        raw_val = row.get('min_gpa')
        print(f"  min_gpa (Cleaned string): '{raw_val}'")
        parsed_val = gpa_parser.parse(raw_val)
        print(f"  parsed float: {parsed_val}")

if __name__ == "__main__":
    main()
