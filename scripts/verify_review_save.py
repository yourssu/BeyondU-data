"""Verify review parsing and persistence against the configured MySQL test DB."""

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


TEST_NAME_ENG = "Review University"
TEST_SEMESTER = "2024-1"


def verify_review_save(database_url: str | None = None) -> None:
    """Write one test row and verify review fields were saved."""
    loader = DatabaseLoader(database_url=database_url)
    loader.create_tables()
    print(f"Using database: {loader.get_display_database_url()}")

    with loader.SessionLocal() as session:
        existing = session.scalars(
            select(University.id).where(
                University.name_eng == TEST_NAME_ENG,
                University.nation == "Review Land",
                University.semester == TEST_SEMESTER,
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
                    University.nation == "Review Land",
                    University.semester == TEST_SEMESTER,
                )
            )
            session.commit()

    df = pd.DataFrame(
        {
            "name_kor": ["Review University KR"],
            "name_eng": [TEST_NAME_ENG],
            "nation": ["Review Land"],
            "program_type": ["교환학생"],
            "semester": [TEST_SEMESTER],
            "institution": ["Review Badge"],
            "min_gpa": ["3.5"],
            "significant_note": ["None"],
            "language_requirement": ["TOEFL 100"],
            "website_url": ["http://review.edu"],
            "available_majors": ["Review Science"],
            "review_raw": ["Y(2023)"],
        }
    )

    print("Loading dataframe into configured MySQL test DB...")
    stats = loader.load_universities_dataframe(df)
    print(f"Load stats: {stats}")

    with loader.SessionLocal() as session:
        uni = session.scalar(
            select(University).where(
                University.name_eng == TEST_NAME_ENG,
                University.nation == "Review Land",
                University.semester == TEST_SEMESTER,
            )
        )

        if not uni:
            print("[FAILURE] University row was not saved.")
            return

        print(f"Found University: {uni.name_eng} / semester={uni.semester}")
        print(f"Has Review: {uni.has_review}")
        print(f"Review Year: '{uni.review_year}'")

        if uni.has_review is True and uni.review_year == "2023":
            print("[SUCCESS] Review data saved successfully.")
        else:
            print(
                "[FAILURE] Review data mismatch. "
                f"Expected (True, '2023'), got ({uni.has_review}, '{uni.review_year}')"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify review persistence in MySQL.")
    parser.add_argument(
        "--database-url",
        help="Optional SQLAlchemy database URL. Defaults to DATABASE_URL from .env.",
    )
    args = parser.parse_args()
    verify_review_save(database_url=args.database_url)
