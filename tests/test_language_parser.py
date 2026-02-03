"""Tests for the updated LanguageParser with float scores."""

import pytest

from src.transform.parser import (
    LANGUAGE_STANDARDS,
    LanguageParser,
    LanguageRequirement,
    ParsedLanguageScore,
    get_score_label,
)


class TestLanguageStandards:
    """Test LANGUAGE_STANDARDS dictionary structure."""

    def test_english_non_europe_codes_exist(self):
        """영어권(비유럽) A1-A5 코드 존재 확인."""
        for code in ["A1", "A2", "A3", "A4", "A5"]:
            assert code in LANGUAGE_STANDARDS
            assert LANGUAGE_STANDARDS[code]["category"] == "english_non_europe"

    def test_europe_english_codes_exist(self):
        """유럽권(영어) EU_A2, EU_B1, EU_B2, EU_C1, EU_C2 코드 존재 확인."""
        for code in ["EU_A2", "EU_B1", "EU_B2", "EU_C1", "EU_C2"]:
            assert code in LANGUAGE_STANDARDS
            assert LANGUAGE_STANDARDS[code]["category"] == "europe_english"

    def test_french_codes_exist(self):
        """프랑스어 D1-D3 코드 존재 확인."""
        for code in ["D1", "D2", "D3"]:
            assert code in LANGUAGE_STANDARDS
            assert LANGUAGE_STANDARDS[code]["category"] == "french"

    def test_german_codes_exist(self):
        """독일어 E1-E3 코드 존재 확인."""
        for code in ["E1", "E2", "E3"]:
            assert code in LANGUAGE_STANDARDS
            assert LANGUAGE_STANDARDS[code]["category"] == "german"

    def test_chinese_codes_exist(self):
        """중국어 B1-B3 코드 존재 확인."""
        for code in ["B1", "B2", "B3"]:
            assert code in LANGUAGE_STANDARDS
            assert LANGUAGE_STANDARDS[code]["category"] == "chinese"

    def test_japanese_codes_exist(self):
        """일본어 C1-C2 코드 존재 확인."""
        for code in ["C1", "C2"]:
            assert code in LANGUAGE_STANDARDS
            assert LANGUAGE_STANDARDS[code]["category"] == "japanese"

    def test_all_scores_are_float(self):
        """모든 점수가 float 타입인지 확인."""
        for code, standard in LANGUAGE_STANDARDS.items():
            for test_type, score in standard["scores"].items():
                assert isinstance(score, float), f"{code}.{test_type} should be float, got {type(score)}"


class TestLanguageParserCodeExpansion:
    """Test LanguageParser code expansion (A2 -> multiple rows)."""

    @pytest.fixture
    def parser(self):
        return LanguageParser()

    def test_parse_a2_expands_to_four_scores(self, parser):
        """A2 코드 입력 시 TOEFL_IBT, IELTS, TOEIC, TOEFL_ITP 4개 행으로 확장."""
        result = parser.parse("A2")

        assert len(result.scores) == 4
        assert all(s.standard_code == "A2" for s in result.scores)

        test_types = {s.test_type for s in result.scores}
        assert test_types == {"TOEFL_IBT", "IELTS", "TOEIC", "TOEFL_ITP"}

        # 점수 검증
        toefl = next(s for s in result.scores if s.test_type == "TOEFL_IBT")
        assert toefl.min_score == 80.0

        ielts = next(s for s in result.scores if s.test_type == "IELTS")
        assert ielts.min_score == 6.0

        toeic = next(s for s in result.scores if s.test_type == "TOEIC")
        assert toeic.min_score == 850.0

    def test_parse_legacy_a_2_with_hyphen(self, parser):
        """A-2 (하이픈 포함) 형식도 A2로 인식."""
        result = parser.parse("A-2")

        assert len(result.scores) == 4
        assert all(s.standard_code == "A2" for s in result.scores)

    def test_parse_b1_chinese(self, parser):
        """B1 (중국어) 코드 파싱."""
        result = parser.parse("B1")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "HSK"
        assert result.scores[0].min_score == 6.0  # 6급
        assert result.scores[0].standard_code == "B1"

    def test_parse_c1_japanese(self, parser):
        """C1 (일본어) 코드 파싱 - JLPT N1 + JPT 900."""
        result = parser.parse("C1")

        assert len(result.scores) == 2
        test_types = {s.test_type for s in result.scores}
        assert test_types == {"JLPT", "JPT"}

        jlpt = next(s for s in result.scores if s.test_type == "JLPT")
        assert jlpt.min_score == 1.0  # N1

        jpt = next(s for s in result.scores if s.test_type == "JPT")
        assert jpt.min_score == 900.0

    def test_parse_d1_french(self, parser):
        """D1 (프랑스어) 코드 파싱 - DELF B2."""
        result = parser.parse("D1")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "DELF"
        assert result.scores[0].min_score == 2.0  # B2 레벨
        assert result.scores[0].standard_code == "D1"

    def test_parse_e2_german(self, parser):
        """E2 (독일어) 코드 파싱 - ZD B1."""
        result = parser.parse("E2")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "ZD"
        assert result.scores[0].min_score == 1.0  # B1 레벨
        assert result.scores[0].standard_code == "E2"


class TestLanguageParserDirectScores:
    """Test LanguageParser direct score parsing."""

    @pytest.fixture
    def parser(self):
        return LanguageParser()

    def test_parse_direct_toefl_score(self, parser):
        """직접 입력: TOEFL 80."""
        result = parser.parse("TOEFL 80")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "TOEFL_IBT"
        assert result.scores[0].min_score == 80.0
        assert result.scores[0].standard_code is None
        assert result.scores[0].source == "direct"

    def test_parse_direct_ielts_score(self, parser):
        """직접 입력: IELTS 6.5."""
        result = parser.parse("IELTS 6.5")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "IELTS"
        assert result.scores[0].min_score == 6.5
        assert result.scores[0].standard_code is None

    def test_parse_direct_toeic_score(self, parser):
        """직접 입력: TOEIC 850."""
        result = parser.parse("TOEIC 850")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "TOEIC"
        assert result.scores[0].min_score == 850.0

    def test_parse_korean_toefl(self, parser):
        """한글 입력: 토플 80."""
        result = parser.parse("토플 80")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "TOEFL_IBT"
        assert result.scores[0].min_score == 80.0

    def test_parse_hsk_with_grade(self, parser):
        """HSK 5급 직접 입력."""
        result = parser.parse("HSK 5급")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "HSK"
        assert result.scores[0].min_score == 5.0

    def test_parse_jlpt_n2(self, parser):
        """JLPT N2 직접 입력."""
        result = parser.parse("JLPT N2")

        assert len(result.scores) == 1
        assert result.scores[0].test_type == "JLPT"
        assert result.scores[0].min_score == 2.0


class TestLanguageParserOptionalAndExcluded:
    """Test optional and excluded language patterns."""

    @pytest.fixture
    def parser(self):
        return LanguageParser()

    def test_parse_optional_no_requirement(self, parser):
        """어학 성적 없음 케이스."""
        result = parser.parse("어학 성적 없음")

        assert result.is_optional is True
        assert len(result.scores) == 0

    def test_parse_optional_na(self, parser):
        """N/A 케이스."""
        result = parser.parse("N/A")

        assert result.is_optional is True

    def test_parse_with_toeic_excluded(self, parser):
        """TOEIC 제외 케이스."""
        result = parser.parse("A2 (TOEIC 제외)")

        assert "TOEIC" in result.excluded_tests
        test_types = {s.test_type for s in result.scores}
        assert "TOEIC" not in test_types
        assert "TOEFL_IBT" in test_types

    def test_parse_with_itp_excluded(self, parser):
        """TOEFL ITP 제외 케이스."""
        result = parser.parse("A2 (ITP 제외)")

        assert "TOEFL_ITP" in result.excluded_tests
        test_types = {s.test_type for s in result.scores}
        assert "TOEFL_ITP" not in test_types


class TestScoreLabelFormatting:
    """Test score label formatting for display."""

    def test_hsk_label(self):
        """HSK 점수 레이블 포맷팅."""
        label = get_score_label("HSK", 6.0)
        assert label == "新HSK 6급"

    def test_jlpt_label(self):
        """JLPT 점수 레이블 포맷팅."""
        label = get_score_label("JLPT", 1.0)
        assert label == "JLPT N1"

    def test_delf_label(self):
        """DELF 점수 레이블 포맷팅."""
        label = get_score_label("DELF", 2.0)
        assert label == "DELF B2"

    def test_ielts_label(self):
        """IELTS 점수 레이블 포맷팅."""
        label = get_score_label("IELTS", 6.5)
        assert label == "IELTS 6.5"

    def test_toefl_label(self):
        """TOEFL 점수 레이블 포맷팅."""
        label = get_score_label("TOEFL_IBT", 80.0)
        assert label == "TOEFL iBT 80"


class TestParserBackwardCompatibility:
    """Test backward compatibility with legacy interface."""

    @pytest.fixture
    def parser(self):
        return LanguageParser()

    def test_requirements_property_returns_dict_list(self, parser):
        """requirements 프로퍼티가 dict 리스트 반환."""
        result = parser.parse("A2")

        assert isinstance(result.requirements, list)
        assert len(result.requirements) == 4
        assert all(isinstance(r, dict) for r in result.requirements)
        assert all("test_type" in r and "score" in r for r in result.requirements)

    def test_parse_to_dict_list(self, parser):
        """parse_to_dict_list 메서드 테스트."""
        result = parser.parse_to_dict_list("A2")

        assert isinstance(result, list)
        assert len(result) == 4
        assert all("test_type" in r and "min_score" in r and "standard_code" in r for r in result)
