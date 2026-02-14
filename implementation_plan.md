# Implementation Plan - Add Badge Column

The user wants to store the "기관" (Institution) information from the Excel file into a new database column called `badge`.

## Proposed Changes

### 1. Database Model (`src/load/models.py`)

Add a new column `badge` to the `University` table.

```python
    # ...
    # [NEW] Badge column mapping to 'institution' from Excel
    badge: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="뱃지 (기관 정보)"
    )
    # ...
```

### 2. Database Loading (`src/load/database.py`)

Update `load_universities_dataframe` to extract `institution` from the DataFrame and map it to `badge`.

```python
                # ...
                data = {
                    "semester": new_semester_from_file,
                    "region": region,
                    "nation": nation,
                    "name_kor": name_kor,
                    "name_eng": name_eng,
                    "badge": self._get_field(row, "institution"), # Map institution to badge
                    # ...
                }
```

### 3. Alembic Migration

Run `alembic revision --autogenerate -m "add_badge_column"` to generate the migration script.
Then `alembic upgrade head` to apply it.

## Verification Plan

1.  **Manual Code Review**: Verify `models.py` and `database.py` changes.
2.  **Migration Generation**: Attempt to generate the migration file using `alembic`.
