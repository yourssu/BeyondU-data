
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.load.database import DatabaseLoader
from src.load.models import University
from sqlalchemy import select

def verify_review_save():
    loader = DatabaseLoader()
    loader.create_tables()
    
    # 1. Create a dummy DataFrame simulating Excel input with 'review_raw' column
    # "review_raw" corresponds to "교환학생수기 여부" in ExcelReader mapping
    df = pd.DataFrame({
        "name_kor": ["리뷰 대학교"],
        "name_eng": ["Review University"],
        "nation": ["Review Land"],
        "program_type": ["교환학생"],
        "semester": ["2024-1"],
        "institution": ["Review Badge"],
        "min_gpa": ["3.5"],
        "significant_note": ["None"],
        "language_requirement": ["TOEFL 100"],
        "website_url": ["http://review.edu"],
        "available_majors": ["Review Science"],
        "review_raw": ["Y(2023)"]  # Expected: has_review=True, review_year="2023"
    })
    
    print("Loading dataframe...")
    stats = loader.load_universities_dataframe(df)
    print(f"Load stats: {stats}")

    # 3. Verify
    with loader.SessionLocal() as session:
        uni = session.scalar(select(University).where(University.name_eng == "Review University"))
        if uni:
            print(f"Found University: {uni.name_eng}")
            print(f"Has Review: {uni.has_review}")
            print(f"Review Year: '{uni.review_year}'")
            
            if uni.has_review is True and uni.review_year == "2023":
                print("[SUCCESS] Review data saved successfully!")
            else:
                print(f"[FAILURE] Review data mismatch. Expected (True, '2023'), got ({uni.has_review}, '{uni.review_year}')")
        else:
            print("[FAILURE] University not found.")

if __name__ == "__main__":
    verify_review_save()
