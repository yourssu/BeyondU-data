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
        "프로그램 구분": "program_type", # 개행문자 제거 후
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
        "지원 자격 최소 학점": "min_gpa", # 로그에서 발견된 헤더 추가
        # Language
        "어학성적": "language_requirement",
        # Notes and Info
        "특이사항": "significant_note",
        "유의사항": "remark",
        "참고사항": "remark_ref",  # Distinguish from remark if needed, or map to same
        "비고": "remark", # remark에 대한 추가 키워드
        "수학가능학과/영어강의목록 등": "available_majors",
        "수학가능학과": "available_majors", # 로그에서 발견된 헤더 추가
        "웹사이트": "website_url",
        "웹사이트 주소": "website_url", # website_url에 대한 추가 키워드
        # Review
        "교환학생수기 여부": "review_raw",
        "수기여부": "review_raw", # review_raw에 대한 추가 키워드
        "FACTSHEET 여부": "review_raw", # 로그에서 Factsheet 여부가 review_raw로 사용되는 것으로 추정
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
                # 파일명이 한글 깨짐을 대비하여 '지원가능대학' 키워드 매칭은 유지하되, 더 유연하게
                if "지원가능대학" in name or "지원가능대학" in str(name).encode('utf-8', 'ignore').decode('utf-8') or name == sheet_names[0]:
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

            # 1. 다중 헤더 처리 (기존 로직)
            if header_row_idx + 1 < len(data):
                next_row = data[header_row_idx + 1]
                if self._is_header_continuation(next_row):
                    headers = self._merge_headers(headers, next_row)
                    df_data = data[header_row_idx + 2 :]

            # 2. [추가] 헤더와 데이터 컬럼 개수 동기화 로직
            if df_data:
                # 실제 데이터 행들 중 가장 긴 행의 길이를 찾음
                max_cols = max(len(row) for row in df_data)
# ._normalize_columns 함수 수정
# ...

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        new_columns: List[str] = []
        for col in df.columns:
            if col is None or pd.isna(col):
                new_columns.append(f"unnamed_{len(new_columns)}")
                continue

            # 컬럼명 강력 정규화
            col_str = str(col)
            col_str = col_str.replace('\n', ' ').replace('\r', ' ').strip() # 개행문자 처리
            col_str = re.sub(r'\s+', ' ', col_str) # 여러 공백을 하나로
            # 불필요한 특수 문자 제거 (한글, 영어, 숫자, 공백, 괄호, 슬래시, 쉼표 제외)
            col_str = re.sub(r'[^\w\s가-힣\(\)/,]', '', col_str)
            col_str = col_str.upper() # 모두 대문자로 변환하여 대소문자 구분 없앰

            mapped = False
            for mapped_key, target_name in self.COLUMN_MAPPING.items():
                # COLUMN_MAPPING의 키도 대문자로 변환하여 비교
                if col_str == mapped_key.upper():
                    new_columns.append(target_name)
                    mapped = True
                    break
            if not mapped:
                new_columns.append(col_str) # 매핑 안 되면 정규화된 이름 사용

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
