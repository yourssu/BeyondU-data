"""Verify one-semester-per-row behavior against the configured MySQL test DB."""

import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, select

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.load.database import DatabaseLoader
from src.load.models import LanguageRequirement, University


TEST_NAME_ENG = "Semester University"
TEST_NATION = "Semester Land"


def verify_semester_1nf(database_url: str | None = None) -> None:
    """Ensure the same university is stored as separate rows per semester."""
    loader = DatabaseLoader(database_url=database_url)
    loader.create_tables()
    print(f"Using database: {loader.get_display_database_url()}")

    with loader.SessionLocal() as session:
        existing = session.scalars(
            select(University.id).where(
                University.name_eng == TEST_NAME_ENG,
                University.nation == TEST_NATION,
            )
        ).all()
        if existing:
            session.execute(
                delete(LanguageRequirement).where(
                    LanguageRequirement.university_id.in_(existing)
                )
            )
            session.execute(
                delete(University).where(
                    University.name_eng == TEST_NAME_ENG,
                    University.nation == TEST_NATION,
                )
            )
            session.commit()

    df = pd.DataFrame(
        [
            {
                "name_kor": "Semester University KR",
                "name_eng": TEST_NAME_ENG,
                "nation": TEST_NATION,
                "program_type": "교환학생",
                "semester": "2024-1",
                "institution": "Semester Badge",
                "min_gpa": "3.5",
                "significant_note": "",
                "language_requirement": "TOEFL 90",
                "website_url": "http://semester.edu",
                "available_majors": "Computer Science",
                "review_raw": "X",
            },
            {
                "name_kor": "Semester University KR",
                "name_eng": TEST_NAME_ENG,
                "nation": TEST_NATION,
                "program_type": "교환학생",
                "semester": "2024-2",
                "institution": "Semester Badge",
                "min_gpa": "3.7",
                "significant_note": "",
                "language_requirement": "TOEFL 95",
                "website_url": "http://semester.edu",
                "available_majors": "Computer Science",
                "review_raw": "Y(2024)",
            },
        ]
    )

    print("Loading multi-semester dataframe into configured MySQL test DB...")
    stats = loader.load_universities_dataframe(df)
    print(f"Load stats: {stats}")

    with loader.SessionLocal() as session:
        universities = session.scalars(
            select(University)
            .where(
                University.name_eng == TEST_NAME_ENG,
                University.nation == TEST_NATION,
            )
            .order_by(University.semester)
        ).all()

    print(f"Saved rows: {len(universities)}")
    for uni in universities:
        print(
            f"  - semester={uni.semester}, min_gpa={uni.min_gpa}, "
            f"has_review={uni.has_review}, review_year={uni.review_year}"
        )

    if len(universities) != 2:
        print("[FAILURE] Expected exactly 2 semester-specific rows.")
        return

    semesters = [uni.semester for uni in universities]
    if semesters != ["2024-1", "2024-2"]:
        print(f"[FAILURE] Unexpected semester rows: {semesters}")
        return

    if any("," in uni.semester for uni in universities):
        print("[FAILURE] Found a comma-joined semester value.")
        return

    print("[SUCCESS] Semester values are normalized to one row per semester.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify one-row-per-semester persistence in MySQL.")
    parser.add_argument(
        "--database-url",
        help="Optional SQLAlchemy database URL. Defaults to DATABASE_URL from .env.",
    )
    args = parser.parse_args()
    verify_semester_1nf(database_url=args.database_url)
