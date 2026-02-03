"""A simple utility script to view data from the database."""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.load.database import DatabaseLoader
from src.load.models import University

def main():
    """Main function to display university and language requirement data."""
    parser = argparse.ArgumentParser(description="View data from the database.")
    parser.add_argument("--limit", type=int, default=20, help="Number of universities to display.")
    parser.add_argument("--output-file", type=Path, help="Path to save the output to a file.")
    args = parser.parse_args()

    # Redirect output if a file is specified
    output_file = None
    if args.output_file:
        output_file = open(args.output_file, "w", encoding="utf-8")
        sys.stdout = output_file

    loader = DatabaseLoader()
    
    with loader.SessionLocal() as session:
        # Fetch universities with a limit
        stmt = select(University).order_by(University.name_kor).limit(args.limit)
        universities = session.execute(stmt).scalars().all()

        if not universities:
            print("No universities found in the database.")
            print("Run the ETL script first: python scripts/run_etl.py --drop-db --init-db")
            return

        print(f"--- Showing Top {len(universities)} Universities ---")

        for i, uni in enumerate(universities):
            gpa = f"GPA: {uni.min_gpa}" if uni.min_gpa else "GPA: N/A"
            semesters = f"Semesters: {uni.available_semester}" if uni.available_semester else ""
            program_types = []
            if uni.is_exchange:
                program_types.append("Exchange")
            if uni.is_visit:
                program_types.append("Visiting")
            program_str = ", ".join(program_types)

            print(f"\n[{i+1}] {uni.name_kor} ({uni.nation}) - {gpa} [{program_str}] {semesters}")
            
            # Print the raw language requirement text
            if uni.language_requirement_text:
                print(f"  Raw Text: {uni.language_requirement_text}")

            # Fetch and display language requirements for each university
            requirements = loader.get_language_requirements(uni.id)
            if requirements:
                print("  Parsed Requirements:")
                for req in requirements:
                    score = f"{req.min_score}" if req.min_score is not None else (req.level_code or "N/A")
                    print(f"  - {req.language_group}/{req.exam_type}: {score}")
            else:
                print("  Parsed Requirements: Not specified or waived.")

    if output_file:
        output_file.close()

if __name__ == "__main__":
    main()
