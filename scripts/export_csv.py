"""Export processed data to CSV for verification."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.extract import ExcelReader
from src.transform import DataCleaner
from src.utils import get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export processed Excel to CSV")
    parser.add_argument("input", type=Path, help="Input Excel file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV file (default: same name as input)",
    )
    args = parser.parse_args()

    # Read and clean
    reader = ExcelReader(args.input)
    df = reader.read()
    cleaner = DataCleaner(df)
    df_clean = cleaner.clean()

    # Determine output path
    output_path = args.output or settings.processed_data_dir / f"{args.input.stem}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export
    df_clean.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(df_clean)} rows to {output_path}")


if __name__ == "__main__":
    main()
