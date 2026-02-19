import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extract.excel_reader import ExcelReader
from src.config import settings

def inspect_headers():
    data_dir = settings.raw_data_dir
    files = sorted(list(data_dir.glob("*.xlsx")))
    
    with open("inspection_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Found {len(files)} files.\n")
        
        for file_path in files[:3]: # Check first 3 files
            if file_path.name.startswith("~"): continue
            f.write(f"\nScanning: {file_path.name}\n")
            try:
                reader = ExcelReader(file_path)
                df = reader.read()
                f.write(f"Mapped Columns: {df.columns.tolist()}\n")
                
                # Check for critical columns
                missing = []
                for req in ["name_kor", "name_eng", "nation"]:
                    if req not in df.columns:
                        missing.append(req)
                
                if missing:
                    f.write(f"WARNING: Missing mapped columns: {missing}\n")
                
                # Show first row
                if not df.empty:
                    f.write(f"First row: {df.iloc[0].to_dict()}\n")
                    
            except Exception as e:
                f.write(f"Error reading {file_path.name}: {e}\n")

if __name__ == "__main__":
    inspect_headers()
