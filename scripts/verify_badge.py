import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.extract.excel_reader import ExcelReader
from src.load.models import University # Just to check field existence

def verify_badge_extraction():
    # Use the latest file
    data_dir = project_root / "data" / "raw"
    files = sorted([f for f in data_dir.glob("*.xlsx") if not f.name.startswith("~$")])
    if not files:
        print("No Excel files found in data/raw")
        return

    latest_file = files[-1]
    print(f"Testing with file: {latest_file.name}")

    reader = ExcelReader(latest_file)
    df = reader.read()
    
    print("\n--- DataFrame Columns ---")
    print(df.columns.tolist())

    if "institution" in df.columns:
        print("\n[SUCCESS] 'institution' column found in DataFrame.")
        print("\n--- Sample Badge Values (mapped locally) ---")
        # Simulating the mapping logic in database.py
        # "badge": self._get_field(row, "institution")
        
        sample_badges = df["institution"].dropna().unique()[:5]
        for badge in sample_badges:
            print(f" - {badge}")
            
        # Check for any nulls if expected
        null_count = df["institution"].isna().sum()
        print(f"\nNull 'institution' count: {null_count}")

    else:
        print("\n[FAILURE] 'institution' column NOT found in DataFrame. Check ExcelReader mapping.")

    # Check Model Definition
    if hasattr(University, 'badge'):
         print("\n[SUCCESS] 'University' model has 'badge' field.")
    else:
         print("\n[FAILURE] 'University' model MISSING 'badge' field.")

if __name__ == "__main__":
    verify_badge_extraction()
