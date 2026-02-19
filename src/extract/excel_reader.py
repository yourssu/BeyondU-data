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
        "국가명": "nation",
        "대학명(국문)": "name_kor",
        "대학명": "name_kor",
        "대학명(영문)": "name_eng",
        "University Name": "name_eng",
        "파견학기": "semester",
        "선발인원": "quota",
        "지원자격": "qualification",
        "지원 자격": "qualification",
        "어학성적": "language_requirement",
        "어학 성적": "language_requirement",
        "지원 자격 어학성적": "language_requirement",
        "GPA": "min_gpa",
        "평점": "min_gpa",
        "최소 학점": "min_gpa",
        "최소학점": "min_gpa",
        "지원 자격 최소 학점": "min_gpa",
        "수학가능전공": "available_majors",
        "수학가능학과": "available_majors",
        "수학가능학과/영어강의목록 등": "available_majors",
        "참고사항": "significant_note",
        "특이사항": "significant_note",
        "특이 사항": "significant_note",
        "유의사항": "significant_note",
        "지원 자격 특이사항": "significant_note",
        "비고": "remark",
        "홈페이지": "website_url",
        "웹사이트": "website_url",
        "Website": "website_url",
        "교환학생수기": "review_raw",
        "교환학생수기 여부": "review_raw",
        "귀국보고서": "review_raw",
        "체험수기": "review_raw",
        "수기": "review_raw",
        "기관": "institution",
        "비고(참조)": "remark_ref",
        "파견가능학기": "available_semester",
        "구분": "program_type",
        "프로그램 구분": "program_type",
    }

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._workbook = None

    def read(self) -> pd.DataFrame:
        """Read the Excel file and return a cleaned DataFrame."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        wb = load_workbook(self.file_path, data_only=True)
        self._workbook = wb
        sheet = wb.active

        data = []
        for row in sheet.rows:
            row_data = []
            for cell in row:
                if isinstance(cell, MergedCell):
                    pass
                row_data.append(cell.value)
            data.append(row_data)

        # 1. Find header row
        header_idx = self._find_header_row(data)
        if header_idx is None:
            raise ValueError(f"Could not find valid header row in {self.file_path.name}")

        # 2. Extract data with header
        # Check for sub-headers in the next row
        headers = [str(x).strip().replace("\n", " ") if x else "" for x in data[header_idx]]
        
        start_row_idx = header_idx + 1
        
        # Heuristic: Check if next row contains specific sub-header keywords
        if header_idx + 1 < len(data):
            next_row_vals = [str(x).strip().replace("\n", " ") if x else "" for x in data[header_idx + 1]]
            sub_keywords = ["최소 학점", "최소학점", "어학성적", "어학 성적", "특이사항"]
            
            if any(k in " ".join(next_row_vals) for k in sub_keywords):
                # Detected sub-headers! Combine them.
                combined_headers = []
                for i, h in enumerate(headers):
                    sub = next_row_vals[i] if i < len(next_row_vals) else ""
                    if not h and sub:
                        combined_headers.append(sub)
                    elif h and sub:
                        combined_headers.append(f"{h} {sub}")
                    elif h:
                        combined_headers.append(h)
                    else:
                        combined_headers.append(f"Unnamed_{i}")
                headers = combined_headers
                start_row_idx = header_idx + 2
            else:
                # Fill empty headers
                headers = [h if h else f"Unnamed_{i}" for i, h in enumerate(headers)]

        body = data[start_row_idx:]

        df = pd.DataFrame(body, columns=headers)

        # 3. Rename columns using mapping
        rename_dict = {}
        for col in df.columns:
            col_clean = str(col).strip().replace("\n", " ")
            
            # Check exact match
            if col_clean in self.COLUMN_MAPPING:
                rename_dict[col] = self.COLUMN_MAPPING[col_clean]
                continue

            # Check if any key is a substring
            matches = []
            for key, val in self.COLUMN_MAPPING.items():
                if key in col_clean:
                    matches.append((key, val))

            if matches:
                # Sort by key length descending to match longest key first
                matches.sort(key=lambda x: len(x[0]), reverse=True)
                rename_dict[col] = matches[0][1]

        df = df.rename(columns=rename_dict)

        # Deduplicate columns to avoid AttributeError in DataCleaner
        new_cols = []
        counts = {}
        for col in df.columns:
            if col in counts:
                counts[col] += 1
                new_cols.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 0
                new_cols.append(col)
        df.columns = new_cols

        # Fill merged cells (forward fill)
        df = df.ffill()

        return df

    def extract_file_metadata(self) -> Dict[str, Any]:
        """Extract metadata from filename."""
        # E.g. "2024-1 교환학생 파견가능대학 및 지원자격(1차).xlsx"
        filename = self.file_path.name

        # Support "2023-1", "2023-여름", etc. at the start of filename
        semester_match = re.search(r"^(\d{4})[-_](\d|여름|겨울)", filename)
        if not semester_match:
             # Try finding pattern anywhere
             semester_match = re.search(r"(\d{4})[-_](\d|여름|겨울)", filename)
        
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
            # Handle newlines in headers for detection
            row_str = " ".join(str(x).upper().replace("\n", " ") for x in row if x is not None and str(x).strip())

            # Check if any search keyword is present in the row string
            if any(keyword in row_str for keyword in search_keywords):
                return i
        return None
