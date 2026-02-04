"""Tests for transform module."""

import pandas as pd
import pytest

from src.transform.cleaner import DataCleaner


class TestDataCleaner:
    """Tests for DataCleaner class."""

    def test_normalize_column_names(self, sample_raw_df: pd.DataFrame) -> None:
        """Test that Korean column names are normalized to English."""
        cleaner = DataCleaner(sample_raw_df)
        df = cleaner.clean()

        assert "country" in df.columns
        assert "university_name" in df.columns
        assert "language_requirement" in df.columns
        assert "gpa_requirement" in df.columns

    def test_removes_empty_rows(self) -> None:
        """Test that rows with missing key fields are removed."""
        df = pd.DataFrame(
            {
                "국가": ["미국", None, "일본"],
                "대학명": ["Harvard", None, "Tokyo"],
            }
        )
        cleaner = DataCleaner(df)
        result = cleaner.clean()

        assert len(result) == 2

    def test_cleans_whitespace(self) -> None:
        """Test that extra whitespace is cleaned."""
        df = pd.DataFrame(
            {
                "국가": ["  미국  ", "일본"],
                "대학명": ["Harvard   University", "Tokyo  University"],
            }
        )
        cleaner = DataCleaner(df)
        result = cleaner.clean()

        assert result.iloc[0]["country"] == "미국"
        assert result.iloc[0]["university_name"] == "Harvard University"

