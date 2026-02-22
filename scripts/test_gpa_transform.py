import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extract.excel_reader import ExcelReader
from src.transform.cleaner import DataCleaner
import pandas as pd

def check_gpa(file_name, target_unis):
    file_path = Path('data/raw') / file_name
    reader = ExcelReader(file_path)
    df = reader.read()
    
    # 1. Before Cleaner
    print(f"\n--- {file_name} (Before Cleaner) ---")
    idx = df['name_eng'].str.contains('|'.join(target_unis), na=False, case=False)
    for _, row in df[idx][['name_eng', 'min_gpa']].iterrows():
        print(row.to_dict())
        
    # 2. After Cleaner
    print(f"\n--- {file_name} (After Cleaner) ---")
    cleaner = DataCleaner(df)
    df_clean = cleaner.clean()
    idx_clean = df_clean['name_eng'].str.contains('|'.join(target_unis), na=False, case=False)
    for _, row in df_clean[idx_clean][['name_eng', 'min_gpa']].iterrows():
        print(row.to_dict())

def main():
    targets = ['Black Hills', 'Colorado State University, Pueblo', 'Minnesota']
    check_gpa('2023-1 교환학생 파견가능대학 및 지원자격(1차).xlsx', targets)
    check_gpa('2025-1 교환학생 파견가능대학 및 지원자격(1차).xlsx', targets)
    check_gpa('2026-2 교환학생 파견가능대학 및 지원자격(1차).xlsx', targets)

if __name__ == "__main__":
    main()
