# Language Requirement Parsing Rules

## Overview
This document outlines the rules for parsing language requirements and exclusions from unstructured text fields (e.g., `significant_note`, `language_requirement`) in the university exchange program data.

## Exclusion Logic
The system identifies universities that explicitly *exclude* certain language tests, even if those tests are generally accepted. This information is typically found in the `significant_note` column.

### Exclusion Patterns
We search for the keyword "제외" (Excl.) and identify the preceding exam names. The following patterns are handled:

1.  **Single Exam Exclusion**
    *   Pattern: `[Exam] 제외`
    *   Example: "ITP 제외" -> `is_excluded=True` for ITP
    *   Example: "TOEIC 제외" -> `is_excluded=True` for TOEIC

2.  **Comma-Separated Exclusions**
    *   Pattern: `[Exam1], [Exam2] 제외`
    *   Example: "TOEIC, ITP 제외" -> `is_excluded=True` for both TOEIC and ITP

3.  **Slash-Separated Exclusions**
    *   Pattern: `[Exam1]/[Exam2] 제외`
    *   Example: "TOEIC/TOEFL ITP 제외" -> `is_excluded=True` for TOEIC and TOEFL ITP

4.  **"Impossible" (불가) Keyword**
    *   Pattern: `[Exam] 불가`
    *   Example: "* TOEIC 불가" -> `is_excluded=True` for TOEIC

5.  **Parentheses with "Excluding"**
    *   Pattern: `([Exam1], [Exam2] 제외)`
    *   Example: "* TOEFL만 인정(IELTS, TOEIC 제외)" -> `is_excluded=True` for IELTS and TOEIC

6.  **Newline Separated**
    *   Pattern: `* [Exam1] 제외 \n * [Exam2] 제외`
    *   Example:
        ```
        * ITP 제외
        * TOEIC 제외
        ```
    *   Result: `is_excluded=True` for ITP and TOEIC

### Handling Specific Cases
*   **Case-Insensitivity**: All matching is case-insensitive (e.g., "toeic" == "TOEIC").
*   **Whitespace**: Extra whitespace around exam names or separators is ignored.
*   **Non-Existent Exams**: If an exclusion pattern matches text that isn't a known exam type (e.g., "TOEFL Home Edition" when we only track "TOEFL"), it is ignored to prevent errors.

## Supported Exam Types
The parsing logic recognizes the following standard exam codes:
*   TOEFL (IBT)
*   TOEFL_ITP (ITP)
*   TOEIC
*   IELTS
*   DUOLINGO
*   HSK
*   JLPT
*   JPT
*   DELF
*   ZD
*   TOPIK

## Implementation Details
*   **Parser Location**: `src/transform/parser.py`
*   **Database Column**: `language_requirement.is_available` (Boolean)
    *   `True`: The test is accepted.
    *   `False`: The test is explicitly excluded (e.g., "ITP 제외").
