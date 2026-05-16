"""A simple utility script to view data from the database."""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.database import DatabaseLoader
from src.load.models import University


def main() -> None:
    """Display university and language requirement data."""
    parser = argparse.ArgumentParser(description="View data from the database.")
    parser.add_argument("--limit", type=int, default=20, help="Number of rows to display.")
    parser.add_argument("--output-file", type=Path, help="Path to save the output.")
    parser.add_argument(
        "--database-url",
        help="Optional SQLAlchemy database URL. Defaults to DATABASE_URL from .env.",
    )
    args = parser.parse_args()

    output_file = None
    if args.output_file:
        output_file = open(args.output_file, "w", encoding="utf-8")
        sys.stdout = output_file

    loader = DatabaseLoader(database_url=args.database_url)
    print(f"Using database: {loader.get_display_database_url()}")

    with loader.SessionLocal() as session:
        stmt = (
            select(University)
            .order_by(University.name_kor, University.semester.desc())
            .limit(args.limit)
        )
        universities = session.execute(stmt).scalars().all()

        if not universities:
            print("No universities found in the database.")
            print("Run the ETL script first: python scripts/run_etl.py --drop-db --init-db")
            return

        print(f"--- Showing Top {len(universities)} University Offerings ---")

        for i, uni in enumerate(universities, start=1):
            gpa = f"GPA: {uni.min_gpa}" if uni.min_gpa else "GPA: N/A"
            program_types = []
            if uni.is_exchange:
                program_types.append("Exchange")
            if uni.is_visit:
                program_types.append("Visiting")
            program_str = ", ".join(program_types) or "Unknown"

            print(
                f"\n[{i}] {uni.name_kor} ({uni.nation}) - "
                f"Semester: {uni.semester} - {gpa} [{program_str}]"
            )

            if uni.language_score:
                print(f"  Raw Text: {uni.language_score}")

            requirements = loader.get_language_requirements(uni.id)
            if requirements:
                print("  Parsed Requirements:")
                for req in requirements:
                    score = f"{req.min_score}" if req.min_score is not None else (
                        req.level_code or "N/A"
                    )
                    print(f"  - {req.language_group}/{req.exam_type}: {score}")
            else:
                print("  Parsed Requirements: Not specified or waived.")

    if output_file:
        output_file.close()


if __name__ == "__main__":
    main()
