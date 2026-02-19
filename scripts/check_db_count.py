import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.database import DatabaseLoader
from src.load.models import University
from sqlalchemy import select, func

def check_db():
    loader = DatabaseLoader()
    with loader.SessionLocal() as session:
        count = session.scalar(select(func.count(University.id)))
        print(f"Total universities in DB: {count}")
        
        # Check a sample
        sample = session.scalars(select(University).limit(5)).all()
        for u in sample:
            print(f"Sample: {u.name_kor} ({u.nation}) - Review: {u.has_review}")

if __name__ == "__main__":
    check_db()
