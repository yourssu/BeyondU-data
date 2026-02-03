"""Pytest fixtures and configuration."""

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    """Sample DataFrame simulating raw Excel data with merged cells already resolved."""
    return pd.DataFrame(
        {
            "국가": ["미국", "미국", "일본", "일본"],
            "대학명": ["Harvard University", "MIT", "Tokyo University", "Kyoto University"],
            "모집인원": ["2명", "3명", "2명", "1명"],
            "어학조건": ["TOEFL IBT 100", "TOEFL IBT 90", "JLPT N1", "어학 성적 없음 가능"],
            "학점조건": ["3.5/4.5", "3.0/4.5", "3.0/4.5", "3.2/4.5"],
            "비고": ["영어권", "공대 우선", None, "일본어 가능자 우대"],
        }
    )


@pytest.fixture
def sample_clean_df() -> pd.DataFrame:
    """Sample cleaned DataFrame with normalized column names."""
    return pd.DataFrame(
        {
            "country": ["미국", "미국", "일본", "일본"],
            "university_name": [
                "Harvard University",
                "MIT",
                "Tokyo University",
                "Kyoto University",
            ],
            "quota": ["2명", "3명", "2명", "1명"],
            "language_requirement": [
                "TOEFL IBT 100",
                "TOEFL IBT 90",
                "JLPT N1",
                "어학 성적 없음 가능",
            ],
            "gpa_requirement": ["3.5/4.5", "3.0/4.5", "3.0/4.5", "3.2/4.5"],
            "notes": ["영어권", "공대 우선", None, "일본어 가능자 우대"],
        }
    )


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
