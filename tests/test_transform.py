"""Tests for transform module."""

import pandas as pd

from src.transform.cleaner import DataCleaner


class TestDataCleaner:
    """Tests for DataCleaner class."""

    def test_removes_empty_rows(self) -> None:
        """Test that rows with missing key fields are removed."""
        df = pd.DataFrame(
            {
                "nation": ["미국", None, "일본"],
                "name_kor": ["Harvard", None, "Tokyo"],
            }
        )
        cleaner = DataCleaner(df)
        result = cleaner.clean()

        assert len(result) == 2

    def test_cleans_whitespace(self) -> None:
        """Test that extra whitespace is cleaned."""
        df = pd.DataFrame(
            {
                "nation": ["  미국  ", "일본"],
                "name_kor": ["Harvard   University", "Tokyo  University"],
            }
        )
        cleaner = DataCleaner(df)
        result = cleaner.clean()

        assert result.iloc[0]["nation"] == "미국"
        assert result.iloc[0]["name_kor"] == "Harvard University"

