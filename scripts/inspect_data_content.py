import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extract.excel_reader import ExcelReader
from src.config import settings
import pandas as pd

def inspect_content():
    data_dir = settings.raw_data_dir
    files = sorted(list(data_dir.glob("*.xlsx")))
    
    with open("inspection_content.txt", "w", encoding="utf-8") as f:
        f.write(f"Found {len(files)} files.\n")
        
        for file_path in files[:3]: # Check first 3 files
            if file_path.name.startswith("~"): continue
            f.write(f"\nScanning: {file_path.name}\n")
            try:
                reader = ExcelReader(file_path)
                df = reader.read()
                f.write(f"Total Rows: {len(df)}\n")
                
                # Check for critical columns
                if "name_eng" in df.columns:
                    null_eng = df["name_eng"].isna().sum()
                    empty_eng = (df["name_eng"] == "").sum()
                    f.write(f"'name_eng' - None: {null_eng}, Empty string: {empty_eng}\n")
                    
                    # Show valid/invalid counts for critical trio
                    valid_mask = df["name_kor"].notna() & df["name_eng"].notna() & df["nation"].notna()
                    f.write(f"Valid Rows (all 3 present): {valid_mask.sum()}\n")
                    f.write(f"Invalid Rows: {(~valid_mask).sum()}\n")
                    
                    if (~valid_mask).sum() > 0:
                        f.write("Sample Invalid Rows:\n")
                        invalid_df = df[~valid_mask].head(5)
                        for idx, row in invalid_df.iterrows():
                            f.write(f"  {idx}: kor={row.get('name_kor')}, eng={row.get('name_eng')}, nation={row.get('nation')}\n")
                else:
                     f.write(f"'name_eng' column MISSING!\n")

            except Exception as e:
                f.write(f"Error reading {file_path.name}: {e}\n")

if __name__ == "__main__":
    inspect_content()
