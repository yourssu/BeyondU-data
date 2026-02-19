"""Parse requirement fields from text to structured data."""

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class ParsedScoreInfo:
    """단일 어학 점수 파싱 결과."""
    exam_type: str
    min_score: float
    level_code: Optional[str]
    language_group: str
    source: str


@dataclass
class ParsedLanguageRequirement:
    """한 대학의 어학 요구사항 전체 파싱 결과."""
    scores: List[ParsedScoreInfo] = field(default_factory=list)
    is_optional: bool = False
    excluded_tests: List[str] = field(default_factory=list)
    raw_text: str = ""


# ============================================================================
# 숭실대학교 공인 어학 성적 기준표 (2024년 기준)
# ============================================================================

LANGUAGE_STANDARDS: Dict[str, Any] = { # Added type hint for LANGUAGE_STANDARDS
    "A1": {"category": "ENGLISH", "scores": {"TOEFL": 85.0, "IELTS": 6.5, "TOEIC": 900.0, "TOEFL_ITP": 600.0}},
    "A2": {"category": "ENGLISH", "scores": {"TOEFL": 80.0, "IELTS": 6.0, "TOEIC": 850.0, "TOEFL_ITP": 560.0}},
    "A3": {"category": "ENGLISH", "scores": {"TOEFL": 75.0, "IELTS": 5.5, "TOEIC": 800.0, "TOEFL_ITP": 545.0}},
    "A4": {"category": "ENGLISH", "scores": {"TOEFL": 70.0, "IELTS": 5.0, "TOEIC": 750.0, "TOEFL_ITP": 530.0}},
    "A5": {"category": "ENGLISH", "scores": {"TOEFL": 60.0, "IELTS": 4.5, "TOEIC": 700.0, "TOEFL_ITP": 515.0}},
    "EU_A2": {"category": "ENGLISH", "scores": {"TOEIC": 225.0}},
    "EU_B1": {"category": "ENGLISH", "scores": {"TOEFL": 42.0, "IELTS": 4.0, "TOEIC": 550.0}},
    "EU_B2": {"category": "ENGLISH", "scores": {"TOEFL": 72.0, "IELTS": 5.5, "TOEIC": 785.0}},
    "EU_C1": {"category": "ENGLISH", "scores": {"TOEFL": 95.0, "IELTS": 6.5, "TOEIC": 945.0}},
    "EU_C2": {"category": "ENGLISH", "scores": {"IELTS": 8.0}},
    "D1": {"category": "FRENCH", "scores": {"DELF": 2.0}},
    "D2": {"category": "FRENCH", "scores": {"DELF": 1.0}},
    "D3": {"category": "FRENCH", "scores": {"DELF": 0.5}},
    "E1": {"category": "GERMAN", "scores": {"ZD": 2.0}},
    "E2": {"category": "GERMAN", "scores": {"ZD": 1.0}},
    "E3": {"category": "GERMAN", "scores": {"ZD": 0.5}},
    "B1": {"category": "CHINESE", "scores": {"HSK": 6.0}},
    "B2": {"category": "CHINESE", "scores": {"HSK": 5.0}},
    "B3": {"category": "CHINESE", "scores": {"HSK": 4.0}},
    "C1": {"category": "JAPANESE", "scores": {"JLPT": 1.0, "JPT": 900.0}},
    "C2": {"category": "JAPANESE", "scores": {"JLPT": 2.0, "JPT": 600.0}},
}

LEGACY_CODE_ALIASES: Dict[str, str] = { # Added type hint for LEGACY_CODE_ALIASES
    "A-1": "A1", "A-2": "A2", "A-3": "A3", "A-4": "A4", "A-5": "A5",
    "B-1": "B1", "B-2": "B2", "B-3": "B3", "C-1": "C1", "C-2": "C2",
    "D-1": "D1", "D-2": "D2", "D-3": "D3", "E-1": "E1", "E-2": "E2", "E-3": "E3",
}

TEST_TYPE_TO_LANGUAGE_GROUP: Dict[str, str] = { # Added type hint for TEST_TYPE_TO_LANGUAGE_GROUP
    "TOEFL": "ENGLISH", "TOEFL_ITP": "ENGLISH", "TOEIC": "ENGLISH",
    "IELTS": "ENGLISH", "DUOLINGO": "ENGLISH",
    "HSK": "CHINESE",
    "JLPT": "JAPANESE", "JPT": "JPT",
    "DELF": "FRENCH",
    "ZD": "GERMAN",
    "TOPIK": "KOREAN",
}

def _cefr_to_float(level_str: str) -> float:
    level_str = level_str.upper().strip()
    mapping = {"B2": 2.0, "B1": 1.0, "A2": 0.5, "A1": 0.25, "C1": 3.0, "C2": 4.0}
    return mapping.get(level_str, 0.0)


class LanguageParser:
    """Parse language requirement text into structured data."""

    SCORE_PATTERNS: List[Tuple[str, str, Callable[[str], float]]] = [ # Added type hint
        (r"TOEFL\s*(?:\(iBT\)|iBT|IBT|ibt)?\s*(\d+)", "TOEFL", lambda x: float(x.replace(',', ''))),
        (r"TOEFL\s*(?:ITP|itp|PBT|pbt)\s*(\d+)", "TOEFL_ITP", lambda x: float(x.replace(',', ''))),
        (r"토플\s*(?:IBT|iBT)?\s*(\d+)", "TOEFL", lambda x: float(x.replace(',', ''))),
        (r"TOEIC\s*([\d,]+)", "TOEIC", lambda x: float(x.replace(',', ''))),
        (r"토익\s*([\d,]+)", "TOEIC", lambda x: float(x.replace(',', ''))),
        (r"(?:IELTS|ITELTS)\s*(\d+\.?\d*)", "IELTS", lambda x: float(x.replace(',', ''))),
        (r"아이엘츠\s*(\d+\.?\d*)", "IELTS", lambda x: float(x.replace(',', ''))),
        (r"Duolingo\s*(\d+)", "DUOLINGO", lambda x: float(x.replace(',', ''))),
        (r"HSK\s*(\d+)급?", "HSK", lambda x: float(x.replace(',', ''))),
        (r"신?HSK\s*(\d+)급?", "HSK", lambda x: float(x.replace(',', ''))),
        (r"JLPT\s*N(\d+)", "JLPT", lambda x: float(x.replace(',', ''))),
        (r"JPT\s*([\d,]+)", "JPT", lambda x: float(x.replace(',', ''))),
        (r"DELF\s*([ABCE])(\d)?", "DELF", lambda x: _cefr_to_float(x)),
        (r"ZD\s*([ABCE])(\d)?", "ZD", lambda x: _cefr_to_float(x)),
        (r"TOPIK\s*(\d+)급?", "TOPIK", lambda x: float(x.replace(',', ''))),
    ]

    EXCLUDE_PATTERNS: List[str] = [r"TOEIC[^가-힣]*제외", r"ITP[^가-힣]*제외", r"토익[^가-힣]*제외"] # Added type hint
    OPTIONAL_PATTERNS: List[str] = [r"어학\s*성적?\s*없음", r"면제", r"불필요", r"N/?A"] # Added type hint

    def parse(self, text: Optional[str], region: Optional[str] = None) -> ParsedLanguageRequirement:
        """
        Parse language requirement text using a direct-first, code-fallback strategy.
        This ensures that scores explicitly mentioned in the text take precedence.
        """
        try:
            import pandas as pd
            if text is None or pd.isna(text):
                return ParsedLanguageRequirement(is_optional=True, raw_text="")
        except ImportError:
            if text is None:
                return ParsedLanguageRequirement(is_optional=True, raw_text="")

        text = str(text).strip()
        if not text:
            return ParsedLanguageRequirement(is_optional=True, raw_text="")

        result = ParsedLanguageRequirement(raw_text=text)
        scores_map: Dict[str, ParsedScoreInfo] = {}

        if any(re.search(p, text, re.IGNORECASE) for p in self.OPTIONAL_PATTERNS):
            result.is_optional = True
            return result

        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if "TOEIC" in pattern or "토익" in pattern:
                    result.excluded_tests.append("TOEIC")
                if "ITP" in pattern:
                    result.excluded_tests.append("TOEFL_ITP")

        # Step 1: Direct parsing first.
        # This finds all explicitly mentioned scores (e.g., "TOEFL 80", "IELTS 6.5")
        # and gives them precedence by adding them to the map first.
        for pattern, exam_type, converter in self.SCORE_PATTERNS:
            if exam_type in result.excluded_tests:
                continue
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    raw_score = match.group(1)
                    if exam_type in ("DELF", "ZD"):
                        # This line is potentially problematic as `match.group(0)` might not always contain the level code directly
                        # Re-evaluate logic if this doesn't work.
                        raw_score = match.group(0).split()[-1]

                    score = converter(raw_score)
                    language_group = TEST_TYPE_TO_LANGUAGE_GROUP.get(exam_type)

                    if score is None or language_group is None:
                        continue

                    # Add or override score in the map.
                    scores_map[exam_type] = ParsedScoreInfo(
                        exam_type=exam_type,
                        min_score=score,
                        level_code=raw_score if exam_type in ("DELF", "ZD") else None,
                        language_group=language_group, # mypy should now infer language_group as str
                        source="direct",
                    )
                except (ValueError, TypeError, IndexError):
                    continue

        # Step 2: Code-based parsing to fill in any missing scores.
        # If a standard code (e.g., "A-4") is found, this provides default scores
        # for any test types that were not explicitly mentioned in the text.
        matched_code = self._match_standard_code(text, region)
        if matched_code and matched_code in LANGUAGE_STANDARDS:
            standard = LANGUAGE_STANDARDS[matched_code]
            lang_group = standard["category"]
            for exam, score in standard["scores"].items():
                # Only add if not already present from direct parsing
                if exam not in scores_map and exam not in result.excluded_tests:
                    scores_map[exam] = ParsedScoreInfo(
                        exam_type=exam,
                        min_score=float(score),
                        level_code=matched_code,
                        language_group=lang_group,
                        source="code",
                    )

        result.scores = list(scores_map.values())
        return result

    def parse_exclusions(self, note: Optional[str]) -> List[str]:
        """
        Parse significant_note to find excluded exams.

        Patterns handled:
        - "ITP 제외"
        - "TOEIC, ITP 제외" (comma)
        - "TOEIC/TOEFL ITP 제외" (slash)
        - "* TOEIC 불가"
        - "* TOEFL만 인정(IELTS, TOEIC 제외)"
        """
        if not note or not str(note).strip():
            return []

        note = str(note)
        excluded_exams = set()

        # Normalize: Remove logic like "단, ..." which might contradict (though "제외" usually takes precedence)
        # But complex sentences like "TOEIC 제외 단, ... 가능" are tricky.
        # We focus on the "제외" or "불가" keyword and the words immediately preceding it.

        # 1. Broad pattern: (Words) + "제외" or "불가"
        # We capture a group of words that look like exam names before "제외"/"불가"
        # \s*[\n,]* handles lists.
        # But precise matching is hard. Let's look for specific patterns.

        # Exams we care about (normalized upper case)
        known_exams = set(TEST_TYPE_TO_LANGUAGE_GROUP.keys())
        # Add some aliases
        known_exams.update(["TOEFL ITP", "TOEFL IBT", "IELTS", "TOEIC"])

        # Strategy: Find "제외" or "불가" and look backwards for exam names
        # OR look for specific exam patterns + "제외"/"불가"

        # Combined regex approach:
        # Look for phrases like "TOEIC, ITP 제외"
        # Pattern: (([A-Za-z]+[A-Za-z0-9_\s]*)(?:[,/]\s*[A-Za-z]+[A-Za-z0-9_\s]*)*)\s*(?:제외|불가)

        # Simplification: Split by lines or major separators, then check each chunk.

        # Let's try the user's suggested simple pattern first and refine.
        # pattern = r"([A-Za-z\s,/]+)\s*제외"

        # We also need to handle Korean text mixed in.
        # Pre-process: Normalize multi-word exams to avoid splitting them
        # "TOEFL ITP" -> "TOEFL_ITP"
        # "TOEFL IBT" -> "TOEFL"
        note_norm = note.upper()
        note_norm = note_norm.replace("TOEFL ITP", "TOEFL_ITP")
        note_norm = note_norm.replace("TOEFL PBT", "TOEFL_ITP")
        note_norm = note_norm.replace("TOEFL IBT", "TOEFL")

        # Use the normalized note for extraction (but be careful about indices if we mapped back to original note,
        # but here we just need the tokens)

        targets = ["제외", "불가"]

        for target in targets:
            # Find all indices of target in NORMALIZED note
            for match in re.finditer(target, note_norm):
                # Look at the text preceding the match (up to, say, 20-30 chars or previous newline/punctuation)
                start = max(0, match.start() - 50)
                prefix = note_norm[start:match.start()]

                # Try to extract exam names from the trailing part of prefix
                # We tokenize the prefix by common separators
                tokens = re.split(r'[,/\s\(\)\[\]]+', prefix)

                # Check tokens in reverse order (closest to "제외" first)
                # Valid exam names usually contain English letters.

                found_in_this_segment = []
                for token in reversed(tokens):
                    clean_token = token.strip() # Already upper from note_norm
                    if not clean_token:
                        continue

                    # Check if it looks like an exam name
                    is_exam = False

                    # Direct match with known exams
                    if clean_token in known_exams:
                        is_exam = True
                    # Common variations
                    elif "ITP" in clean_token:
                        found_in_this_segment.append("TOEFL_ITP") # Normalize ITP -> TOEFL_ITP
                        continue
                    elif "IBT" in clean_token:
                        found_in_this_segment.append("TOEFL")
                        continue

                    if is_exam:
                        found_in_this_segment.append(clean_token)
                    else:
                        # If we hit a non-exam word (e.g. "어학성적", "단,"), specifically if it's Korean or unrelated English
                        # we should probably stop for this segment to avoid "Eating" too far back.
                        # Heuristic: If it contains Korean, stop.
                        if re.search(r'[가-힣]', token):
                            break
                        # If it's a very long word or irrelevant, maybe stop?
                        # For now, simplistic check: if not in KNOWN and not similar, stop.
                        pass

                excluded_exams.update(found_in_this_segment)

        return list(excluded_exams)

    def _match_standard_code(self, text: str, region: Optional[str] = None) -> Optional[str]:
        """Extracts a standard grade code from the text."""
        text_upper = text.upper().strip()

        # Region-specific logic (Europe)
        if region and '유럽' in region:
            # English B1/B2 for Europe -> EU_B1/EU_B2
            # Match "영어 B2", "English B1" etc.
            if '영어' in text or 'english' in text_upper:
                b_match = re.search(r'\b(B[12])\b', text_upper)
                if b_match:
                    code = f"EU_{b_match.group(1)}"
                    if code in LANGUAGE_STANDARDS:
                        return code

        # EU_B1, EU_B2 etc.
        eu_match = re.search(r'\b(EU_[ABC][12])\b', text_upper)
        if eu_match and eu_match.group(1) in LANGUAGE_STANDARDS:
            return eu_match.group(1)

        # A-1, B-2 etc.
        hyphen_match = re.search(r'\b([A-E]-[1-5])\b', text_upper)
        if hyphen_match and hyphen_match.group(1) in LEGACY_CODE_ALIASES:
            return LEGACY_CODE_ALIASES[hyphen_match.group(1)]

        # A1, B2, C1 etc.
        simple_match = re.search(r'\b([A-E][1-5])\b', text_upper)
        if simple_match and simple_match.group(1) in LANGUAGE_STANDARDS:
            return simple_match.group(1)

        return None

class GPAParser:
    """Parse GPA requirements."""

    def parse(self, text: Optional[str]) -> Optional[float]:
        """Parse GPA requirement text and return a float, assuming a 4.5 scale."""
        if text is None:
            return None

        text = str(text).strip()
        if not text:
            return None

        # Extracts the first number found, which is assumed to be the GPA.
        match = re.search(r"(\d+\.?\d*)", text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                return None

        return None


class WebsiteURLParser:
    """Parse and clean website URL strings."""

    def parse(self, text: Optional[str]) -> Optional[str]:
        """
        Parses a string to find and clean the first URL.
        Handles various formats including those without protocols.
        """
        if not text or not str(text).strip():
            return None

        text_str = str(text).strip()

        # 1. First pass: Look for URLs starting with a protocol or 'www.'
        # This is more reliable. Stops at whitespace or common closing brackets.
        match = re.search(r"(https?://|www\.)[^\s()\[\]\{\}]+", text_str)

        # 2. Second pass: If nothing found, look for domain-like patterns (e.g., example.com)
        if not match:
            # This looks for "word.word" patterns that are likely domains.
            # It avoids matching floating point numbers by requiring a letter in the TLD.
            match = re.search(r"\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:[/\?#][^\s()\[\]\{\}]+)?\b", text_str)
            if not match:
                return None

        url = match.group(0)

        # Ensure the URL has a protocol for consistency.
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        return url

class ReviewParser:
    """Parse exchange student review availability and year."""

    def parse(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Parse review text to extract availability and year.

        Examples:
            "Y(2018)" -> (True, "2018")
            "Y(2013-2019)" -> (True, "2013-2019")
            "2018" -> (True, "2018")
            "O" -> (True, None)
            "Yes" -> (True, None)
            "X" -> (False, None)
            None -> (False, None)
        """
        if not text or not str(text).strip():
            return False, None

        text_str = str(text).strip()
        text_upper = text_str.upper()

        # Negative cases
        if text_upper in ("X", "N", "NO", "NONE", "-"):
            return False, None

        # Logic:
        # 1. Look for year pattern (4 digits, or range like 2013-2019)
        # 2. If year found, assume True.
        # 3. If no year, check for positive indicators (Y, O, YES, EXIST, etc.)

        # Year pattern: 20xx or 20xx-20xx
        year_match = re.search(r"(20\d{2}(?:\s*-\s*20\d{2})?)", text_str)
        if year_match:
            return True, year_match.group(1).strip()

        # Positive indicators
        # Starts with Y, O, or is "있음", "존재", etc.
        positive_keywords = ["Y", "O", "YES", "TRUE", "AVAILABLE", "있음", "후기", "수기"]

        # Check if it starts with any positive keyword or matches exactly
        for keyword in positive_keywords:
            if text_upper.startswith(keyword):
                return True, None

        # If it's just some non-negative text, valid review might be implied?
        # But let's be conservative. If it's not X and doesn't have Year,
        # but has some content...
        # Let's stick to explicit positive start or year presence.

        return False, None
