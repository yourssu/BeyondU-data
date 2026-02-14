
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.load.database import DatabaseLoader
from src.load.models import University
from sqlalchemy import select

def verify_badge_save():
    loader = DatabaseLoader()
    
    # 1. Create a dummy DataFrame simulating Excel input with 'Badge' column
    data = {
        "nation": ["Moon"],
        "university_name": ["Moon University"],
        "institution": ["Space Badge"], # This maps to 'badge' in DB
        "gpa_requirement": [3.5],
        "notes": ["None"],
        "language_requirement": ["TOEFL 100"],
    }
    # Note: 'institution' in clean DF maps to 'badge' field in DB model via DatabaseLoader logic
    # DatabaseLoader receives 'institution' key from DF and saves it as 'badge' attribute.
    # checking create_tables just in case
    loader.create_tables()

    # 2. Use loader to save
    # We need to mimic the clean dataframe structure expected by load_universities_dataframe
    # The columns expected are normalized ones.
    # Let's check keys used in load_universities_dataframe:
    # name_kor, name_eng, nation, program_type, semester, institution (mapped to badge), etc.
    
    df = pd.DataFrame({
        "name_kor": ["달 대학교"],
        "name_eng": ["Moon University"],
        "nation": ["Moon"],
        "program_type": ["교환학생"],
        "semester": ["2024-1"],
        "institution": ["Space Badge"], # This should be saved as badge
        "min_gpa": ["3.5"],
        "significant_note": ["None"],
        "language_requirement": ["TOEFL 100"],
        "website_url": ["http://moon.edu"],
        "available_majors": ["Space Science"],
        "review_raw": ["X"]
    })
    
    print("Loading dataframe...")
    stats = loader.load_universities_dataframe(df)
    print(f"Load stats: {stats}")

    # 3. Verify
    with loader.SessionLocal() as session:
        uni = session.scalar(select(University).where(University.name_eng == "Moon University"))
        if uni:
            print(f"Found University: {uni.name_eng}")
            print(f"Badge Value: '{uni.badge}'")
            if uni.badge == "Space Badge":
                print("[SUCCESS] Badge saved successfully!")
            else:
                print(f"[FAILURE] Badge mismatch. Expected 'Space Badge', got '{uni.badge}'")
        else:
            print("[FAILURE] University not found.")

if __name__ == "__main__":
    verify_badge_save()
