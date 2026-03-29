import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.database import DatabaseLoader
from src.load.models import University, LanguageRequirement
from sqlalchemy import select, func

def check_values():
    loader = DatabaseLoader()
    with loader.SessionLocal() as session:
        # Total count
        count = session.scalar(select(func.count(University.id)))
        print(f"Total universities: {count}")
        
        # Check new fields
        loc_count = session.scalar(select(func.count(University.id)).where(University.location.is_not(None)))
        std_count = session.scalar(select(func.count(University.id)).where(University.student_count.is_not(None)))
        maj_count = session.scalar(select(func.count(University.id)).where(University.available_major.is_not(None)))
        sub_count = session.scalar(select(func.count(University.id)).where(University.available_subject.is_not(None)))
        
        print(f"Universities with location: {loc_count}")
        print(f"Universities with student_count: {std_count}")
        print(f"Universities with available_major: {maj_count}")
        print(f"Universities with available_subject: {sub_count}")
        
        # Language requirements check
        lang_count = session.scalar(select(func.count(LanguageRequirement.id)))
        print(f"Total language requirements: {lang_count}")
        
        # Sample non-null values
        sample = session.scalars(select(University).where(University.location.is_not(None)).limit(3)).all()
        print("\n--- Samples with Location ---")
        for u in sample:
            print(f"[{u.name_kor}]")
            print(f"  Location: {u.location}")
            print(f"  Students: {u.student_count}")
            print(f"  Major: {u.available_major[:50] if u.available_major else 'None'}...")
            print(f"  Subject URL: {u.available_subject}")
            print(f"  Created At: {u.created_at}")
            print(f"  Updated At: {u.updated_at}")

if __name__ == "__main__":
    check_values()
