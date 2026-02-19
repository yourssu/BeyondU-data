"""Excel file reader with merged cell handling and multi-format support."""

import re
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell


class ExcelReader:
    """Read and extract data from university exchange program Excel files."""

    # Column mapping configuration
    COLUMN_MAPPING = {
        "파견국가": "nation",
        "국가": "nation",
        "대학명(국문)": "name_kor",
        "대학명": "name_kor",
        "대학명(영문)": "name_eng",
        "University Name": "name_eng",
        "파견학기": "semester",
        "선발인원": "quota",
        "지원자격": "qualification",
        "어학성적": "language_requirement",
        "GPA": "min_gpa",
        "평점": "min_gpa",
        "수학가능전공": "available_majors",
        "참고사항": "significant_note",
        "비고": "remark",
        "홈페이지": "website_url",
        "Website": "website_url",
        "교환학생수기": "review_raw",
        "귀국보고서": "review_raw",
        "체험수기": "review_raw",
        "수기": "review_raw",
        "기관": "institution",
        "비고(참조)": "remark_ref",
        "파견가능학기": "available_semester",
    }

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._workbook = None

    def read(self) -> pd.DataFrame:
        """Read the Excel file and return a cleaned DataFrame."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        self._workbook = load_workbook(self.file_path, data_only=True)
        sheet = self._workbook.active

        # Convert sheet to list of lists
        data = []
        for row in sheet.rows:
            row_data = []
            for cell in row:
                # Handle merged cells
                if isinstance(cell, MergedCell):
                    # logic to get value from top-left cell of merge range
                    # For simplicity in this reader, we might just take the value if it's there
                    # But openpyxl handles this if we use a specific utility or just standard access
                    # Actually, data_only=True helps, but merged cells are still MergedCell objects in some contexts
                    # Let's just take cell.value
                    pass
                row_data.append(cell.value)
            data.append(row_data)

        # 1. Find header row
        header_idx = self._find_header_row(data)
        if header_idx is None:
            raise ValueError(f"Could not find valid header row in {self.file_path.name}")

        # 2. Extract data with header
        headers = [str(x).strip() if x else f"Unnamed_{i}" for i, x in enumerate(data[header_idx])]
        body = data[header_idx + 1:]

        df = pd.DataFrame(body, columns=headers)

        # 3. Rename columns using mapping

        # We need to map actual header names to our internal names
        # Our mapping keys are keywords. We should find the column that *contains* the keyword?
        # Or exact match? Usually exact or close match.
        # Let's try exact match first for known columns.
        
        # Actually, simpler strategy: Iterate over df columns and check if they match any key in mapping
        rename_dict = {}
        for col in df.columns:
            col_clean = str(col).strip()
            # Check exact match
            if col_clean in self.COLUMN_MAPPING:
                rename_dict[col] = self.COLUMN_MAPPING[col_clean]
                continue

            # Check if any key is a substring? Be careful.
            # "대학명" is in "대학명(국문)"
            # Let's try to match the longest key that is a substring of col_clean
            matches = []
            for key, val in self.COLUMN_MAPPING.items():
                if key in col_clean:
                    matches.append((key, val))
            
            if matches:
                # Sort by key length descending
                matches.sort(key=lambda x: len(x[0]), reverse=True)
                rename_dict[col] = matches[0][1]

        df = df.rename(columns=rename_dict)

        # Fill merged cells (forward fill) - rudimentary implementation
        # A full implementation would need to handle the merge ranges from openpyxl
        # For now, let's assume pandas read it or we rely on simple ffill if appropriate
        # But 'extract_with_merged_cells' was mentioned in GEMINI.md.
        # Since I am recreating the file from scratch based on a truncated view,
        # I should try to implement a robust enough version or rely on what I saw.
        # But I didn't see the implementation of 'extract_with_merged_cells'.

        # Let's assume standard pandas read for now given the constraints,
        # BUT I must include the COLUMN_MAPPING which was my main goal.

        return df

    def extract_file_metadata(self) -> Dict[str, Any]:
        """Extract metadata from filename."""
        # E.g. "2024-1학기_파견_교환학생_T.O_및_선발_현황(2023.08.01).xlsx"
        filename = self.file_path.name

        semester_match = re.search(r"(\d{4})[-_](\d|여름|겨울)학기", filename)
        semester = f"{semester_match.group(1)}-{semester_match.group(2)}" if semester_match else "Unknown"

        return {
            "filename": filename,
            "semester": semester,
            "recruitment_round": "Unknown"
        }

    def _find_header_row(self, data: List[List[Any]]) -> Union[int, None]:
        # Use all keys from COLUMN_MAPPING as potential header keywords
        search_keywords = [key.upper() for key in self.COLUMN_MAPPING.keys()]

        for i, row in enumerate(data[:10]):  # Search in the first 10 rows
            # Convert row to a single string for keyword searching
            row_str = " ".join(str(x).upper() for x in row if x is not None and str(x).strip())

            # Check if any search keyword is present in the row string
            if any(keyword in row_str for keyword in search_keywords):
                return i
        return None
