import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.database import DatabaseLoader
from src.load.models import University
from sqlalchemy import select, func

def check_values():
    loader = DatabaseLoader()
    with loader.SessionLocal() as session:
        # Total count
        count = session.scalar(select(func.count(University.id)))
        print(f"Total universities: {count}")
        
        # Check 'Unknown' semester
        unknown_semester = session.scalar(select(func.count(University.id)).where(University.semester == 'Unknown'))
        print(f"Universities with 'Unknown' semester: {unknown_semester}")
        
        # Check min_gpa > 0
        valid_gpa = session.scalar(select(func.count(University.id)).where(University.min_gpa > 0))
        print(f"Universities with min_gpa > 0: {valid_gpa}")
        
        # Check available_majors not null
        valid_majors = session.scalar(select(func.count(University.id)).where(University.available_majors.is_not(None)))
        print(f"Universities with available_majors: {valid_majors}")
        
        # Sample non-null values
        sample = session.scalars(select(University).limit(5)).all()
        for u in sample:
            print(f"[{u.name_kor}] Sem: {u.semester}, GPA: {u.min_gpa}, Major: {u.available_majors[:30] if u.available_majors else 'None'}..., Review: {u.has_review}")

if __name__ == "__main__":
    check_values()
