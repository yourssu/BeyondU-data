# Implementation Plan - Add Review Status and Year

The user wants to track exchange student review availability.
We need to parse the "교환학생수기 여부" column (e.g., "Y(2018)", "X") into two columns:
1.  `has_review` (Boolean): True if it starts with 'Y'.
2.  `review_year` (String): The content inside parentheses (e.g., "2018", "2013-2019"), or NULL.

## Proposed Changes

### 1. Database Model (`src/load/models.py`)
Add new columns to `University` table:
```python
    has_review: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="교환학생 수기 존재 여부"
    )
    review_year: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="수기 연도 (예: 2018, 2013-2019)"
    )
```

### 2. Excel Extraction (`src/extract/excel_reader.py`)
Add mapping for the raw column:
```python
    COLUMN_MAPPING = {
        # ...
        "교환학생수기 여부": "review_raw",
        # ...
    }
```

### 3. Parsing Logic (`src/transform/parser.py`)
Create `ReviewParser` class:
```python
class ReviewParser:
    def parse(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        # Returns (has_review, review_year)
        # Logic:
        # 1. If starts with 'Y': has_review = True
        # 2. Extract text between '(' and ')' for review_year
```

### 4. Database Loading (`src/load/database.py`)
Update `load_universities_dataframe`:
*   Instantiate `ReviewParser`.
*   Call `parser.parse(row['review_raw'])`.
*   Populate `has_review` and `review_year` in the `University` object.

## Verification
*   Create `scripts/verify_reviews.py` to check the database table for correct parsing of "Y(2018)" and "X" cases.
