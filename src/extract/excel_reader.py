"""Excel file reader with merged cell handling and multi-format support."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import pandas as pd
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell

from src.config import settings


class ExcelReader:
    """Read and extract data from university exchange program Excel files."""

    # Header row patterns for different file versions
    HEADER_KEYWORDS = ["대학명", "국가명", "프로그램", "구분", "일련번호"]

    # Column name normalization mapping
    COLUMN_MAPPING = {
        # Program type
        "프로그램 구분": "program_type",
        "프로그램\n구분": "program_type",
        "구분": "program_type",
        # Institution
        "기관": "institution",
        # Region/Country
        "지역": "region",
        "국가명": "nation",
        # University names
        "대학명(한글)": "name_kor",
        "대학명(국문)": "name_kor",
        "대학명(영문)": "name_eng",
        # GPA
        "최소 학점": "min_gpa",
        "지원 자격": "min_gpa",
        # Language
        "어학성적": "language_requirement",
        # Notes and Info
        "특이사항": "remark",
        "유의사항": "remark",
        "참고사항": "remark",
        "비고": "remark",
        "수학가능학과/영어강의목록 등": "available_majors",
        "웹사이트 ": "website_url",
        "웹사이트": "website_url",
    }

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self._workbook = None

    def read(self, sheet_name: Union[str, None] = None) -> pd.DataFrame:
        """
        Read Excel file and return DataFrame with merged cells resolved.
        """
        # Load workbook to handle merged cells
        wb = load_workbook(self.file_path)

        # Determine which sheet to read
        if sheet_name:
            ws = wb[sheet_name]
        else:
            sheet_names = wb.sheetnames
            main_sheet = None
            for name in sheet_names:
                if "지원가능대학" in name or name == sheet_names[0]:
                    main_sheet = name
                    break
            ws = wb[main_sheet or sheet_names[0]]

        if ws is None:
            raise ValueError(f"No sheet found in {self.file_path}")

        merged_ranges = list(ws.merged_cells.ranges)
        data = self._extract_with_merged_cells(ws, merged_ranges)
        wb.close()

        if not data:
            return pd.DataFrame()

        header_row_idx = self._find_header_row(data)

        if header_row_idx is not None:
            headers = data[header_row_idx]
            df_data = data[header_row_idx + 1 :]
            if header_row_idx + 1 < len(data):
                next_row = data[header_row_idx + 1]
                if self._is_header_continuation(next_row):
                    headers = self._merge_headers(headers, next_row)
                    df_data = data[header_row_idx + 2 :]
            df = pd.DataFrame(df_data, columns=headers)
        else:
            df = pd.DataFrame(data[1:], columns=data[0])

        df = self._normalize_columns(df)
        metadata = self.extract_file_metadata()
        if metadata["semester"]:
            df["semester"] = metadata["semester"]
        df = self._clean_dataframe(df)
        return df

    def _extract_with_merged_cells(self, ws: Any, merged_ranges: List[Any]) -> List[List[Any]]:
        merged_cell_map: Dict[Tuple[int, int], Any] = {}
        for merged_range in merged_ranges:
            min_row, min_col = merged_range.min_row, merged_range.min_col
            value = ws.cell(row=min_row, column=min_col).value
            for row in range(merged_range.min_row, merged_range.max_row + 1):
                for col in range(merged_range.min_col, merged_range.max_col + 1):
                    merged_cell_map[(row, col)] = value
        data: List[List[Any]] = []
        for row_idx, row in enumerate(ws.iter_rows(), start=1):
            row_data: List[Any] = []
            for col_idx, cell in enumerate(row, start=1):
                value = merged_cell_map.get((row_idx, col_idx)) if isinstance(cell, MergedCell) else cell.value
                row_data.append(value)
            data.append(row_data)
        return data

    def _find_header_row(self, data: List[List[Any]]) -> Union[int, None]:
        for i, row in enumerate(data[:10]):
            row_str = " ".join(str(x) for x in row if x)
            if any(keyword in row_str for keyword in self.HEADER_KEYWORDS):
                return i
        return None

    def _is_header_continuation(self, row: List[Any]) -> bool:
        non_empty = [x for x in row if x and str(x).strip()]
        if len(non_empty) <= 5:
            for val in non_empty:
                if any(kw in str(val) for kw in ["최소 학점", "어학성적", "특이사항"]):
                    return True
        return False

    def _merge_headers(self, header1: List[Any], header2: List[Any]) -> List[Any]:
        merged = []
        for h1, h2 in zip(header1, header2):
            if h1 and str(h1).strip():
                merged.append(h1)
            elif h2 and str(h2).strip():
                merged.append(h2)
            else:
                merged.append(None)
        return merged

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        new_columns: List[str] = []
        for col in df.columns:
            if col is None or pd.isna(col):
                new_columns.append(f"unnamed_{len(new_columns)}")
                continue
            col_str = str(col).strip()
            if col_str in self.COLUMN_MAPPING:
                new_columns.append(self.COLUMN_MAPPING[col_str])
            else:
                new_columns.append(col_str)
        df.columns = pd.Index(new_columns)
        cols = pd.Series(df.columns)
        if cols.duplicated().any():
            for dup_name in cols[cols.duplicated()].astype(str).unique():
                dup_cols = df.columns[cols == dup_name]
                df[dup_cols[0]] = df[dup_cols].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
                df = df.drop(columns=dup_cols[1:]).copy()
        return df

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(how="all")
        if "institution" in df.columns and settings.excluded_institutions:
            df = df[~df["institution"].isin(settings.excluded_institutions)]
        if "name_kor" in df.columns:
            df = df[df["name_kor"].notna()]
            df = df[~df["name_kor"].astype(str).str.contains("합계|소계|총계|대학명|개국", na=False)]
        merge_columns = ["nation", "region", "program_type", "institution"]
        for col in merge_columns:
            if col in df.columns:
                df[col] = df[col].ffill()
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else x)
        return df.reset_index(drop=True)

    def get_sheet_names(self) -> List[str]:
        wb = load_workbook(self.file_path, read_only=True)
        names = wb.sheetnames
        wb.close()
        return cast(List[str], names)

    def extract_file_metadata(self) -> Dict[str, Optional[str]]:
        filename = self.file_path.stem
        semester_match = re.search(r"(\d{4})-?(\d)", filename)
        semester = f"{semester_match.groups()[0]}-{semester_match.groups()[1]}" if semester_match else None
        round_match = re.search(r"(\d)차", filename)
        recruitment_round = f"{round_match.group(1)}차" if round_match else None
        return {"semester": semester, "recruitment_round": recruitment_round, "filename": self.file_path.name}
