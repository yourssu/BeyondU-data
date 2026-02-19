"""Main ETL pipeline runner."""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

import logging
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.extract import ExcelReader
from src.load import DatabaseLoader
from src.transform import DataCleaner
from src.utils import get_logger

logger = get_logger(__name__, level=logging.DEBUG)


def process_file(
    file_path: Path,
    loader: DatabaseLoader,
    dry_run: bool = False,
) -> Dict[str, int]:
    """Process a single Excel file through the ETL pipeline."""
    logger.info(f"Processing: {file_path.name}")

    # Extract
    reader = ExcelReader(file_path)
    df = reader.read()
    metadata = reader.extract_file_metadata()

    logger.info(f"  Extracted {len(df)} rows")
    logger.info(f"  Metadata: semester={metadata['semester']}, round={metadata['recruitment_round']}")

    # Inject metadata into DataFrame
    # This is crucial because DatabaseLoader expects 'semester' in the DataFrame
    for key, value in metadata.items():
        if key not in df.columns:
            df[key] = value

    if len(df) == 0:
        logger.warning(f"  No data extracted from {file_path.name}")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    # Transform
    cleaner = DataCleaner(df)
    df_clean = cleaner.clean()
    logger.info(f"  Cleaned to {len(df_clean)} rows")

    # Show sample data
    if len(df_clean) > 0:
        logger.info(f"  Columns: {list(df_clean.columns)}")
        logger.info(f"  Sample row: {df_clean.iloc[0].to_dict()}")

    if dry_run:
        logger.info("  [DRY RUN] Skipping database load")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    # Load
    stats = loader.load_universities_dataframe(df_clean)
    logger.info(f"  Loaded: {stats}")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ETL pipeline for exchange data")
    parser.add_argument(
        "--input",
        type=Path,
        default=settings.raw_data_dir,
        help="Input directory or file path",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Process a single file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without loading to database",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database tables",
    )
    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="Drop and recreate database tables",
    )
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Only process the latest file (by filename)",
    )
    args = parser.parse_args()

    # Initialize database
    loader = DatabaseLoader()

    if args.drop_db:
        logger.info("Dropping database tables...")
        loader.drop_tables()

    if args.init_db or args.drop_db:
        logger.info("Initializing database tables...")
        loader.create_tables()
        logger.info("Database tables created")

    # Determine files to process
    if args.file:
        files = [args.file]
    elif args.input.is_dir():
        all_files = list(args.input.glob("*.xlsx")) + list(args.input.glob("*.xls"))
        # Filter out temporary Excel files (starting with ~$)
        files = sorted([f for f in all_files if not f.name.startswith("~")])
    else:
        files = [args.input]

    if not files:
        logger.warning("No Excel files found to process")
        return

    if args.latest_only and len(files) > 1:
        files = [files[-1]]
        logger.info(f"Processing only the latest file: {files[0].name}")

    logger.info(f"Files to process: {[f.name for f in files]}")

    # Process files
    total_stats = {"inserted": 0, "updated": 0, "skipped": 0}

    for file_path in files:
        try:
            stats = process_file(file_path, loader, dry_run=args.dry_run)
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()
            continue

    logger.info(f"ETL Complete. Total: {total_stats}")


if __name__ == "__main__":
    main()
