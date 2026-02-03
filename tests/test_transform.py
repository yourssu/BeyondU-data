"""Tests for transform module."""

import pandas as pd
import pytest

from src.transform.cleaner import DataCleaner
from src.transform.parser import RequirementParser


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


class TestRequirementParser:
    """Tests for RequirementParser class."""

    @pytest.fixture
    def parser(self) -> RequirementParser:
        return RequirementParser()

    def test_parse_toefl_ibt(self, parser: RequirementParser) -> None:
        """Test parsing TOEFL IBT scores."""
        result = parser.parse_language_requirement("TOEFL IBT 100")
        assert result.test_type == "TOEFL_IBT"
        assert result.min_score == 100
        assert result.is_optional is False

    def test_parse_toeic(self, parser: RequirementParser) -> None:
        """Test parsing TOEIC scores."""
        result = parser.parse_language_requirement("TOEIC 800점 이상")
        assert result.test_type == "TOEIC"
        assert result.min_score == 800

    def test_parse_ielts(self, parser: RequirementParser) -> None:
        """Test parsing IELTS scores."""
        result = parser.parse_language_requirement("IELTS 6.5")
        assert result.test_type == "IELTS"
        assert result.min_score == 6.5

    def test_parse_jlpt(self, parser: RequirementParser) -> None:
        """Test parsing JLPT levels."""
        result = parser.parse_language_requirement("JLPT N1")
        assert result.test_type == "JLPT"
        assert result.min_score == 1

    def test_parse_optional_language(self, parser: RequirementParser) -> None:
        """Test parsing optional language requirement."""
        result = parser.parse_language_requirement("어학 성적 없음 선택 가능")
        assert result.is_optional is True

    def test_parse_gpa_with_scale(self, parser: RequirementParser) -> None:
        """Test parsing GPA with scale."""
        result = parser.parse_gpa_requirement("3.5/4.5")
        assert result.min_gpa == 3.5
        assert result.max_scale == 4.5

    def test_parse_gpa_text_format(self, parser: RequirementParser) -> None:
        """Test parsing GPA in text format."""
        result = parser.parse_gpa_requirement("평점 3.0 이상")
        assert result.min_gpa == 3.0

    def test_parse_quota(self, parser: RequirementParser) -> None:
        """Test parsing quota numbers."""
        assert parser.parse_quota("2명") == 2
        assert parser.parse_quota("10") == 10
        assert parser.parse_quota(None) is None
