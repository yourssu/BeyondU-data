# Excel Reader Refactoring Plan

## 1. Goal Description
The goal is to simplify `src/extract/excel_reader.py` because the raw Excel files now have a uniform header format. The complex sub-header merging logic can be removed.
Additionally, 2023 Excel files lack the "지역" (region) column. We need to handle this exception by referencing other data (e.g., a 2024 or 2025 file) to populate the "지역" column based on the "국가" (nation/country).

## 2. Proposed Changes

### `src/extract/excel_reader.py`
- Remove the heuristic logic that merges two header rows (`if header_idx + 1 < len(data): ...`).
- Keep simply `headers = data[header_idx]` and `start_row_idx = header_idx + 1`.
- Add `"지역": "region"` to `COLUMN_MAPPING`.
- In `read()`, handle the 2023 exception: 
  - If `"2023" in self.file_path.name` and `"region"` is missing from columns:
    - Load a reference Excel file (e.g., `2024-1 교환학생 파견가능대학 및 지원자격(1차).xlsx` or any non-2023 file in the same directory).
    - Read the reference file's `국가`/`파견국가` -> `지역` mapping.
    - Map the `nation` column of the 2023 dataframe to fill the `region` column.

## 3. Verification Plan
- **Automated Tests**:
  - Run `python scripts/run_etl.py --dry-run` to test the full extraction process without affecting the DB. It should process all 2023-2026 files successfully, and print out logs indicating that "region" is present in the extracted dataframes.
- **Manual Verification**:
  - Add debug prints or logs to confirm that for 2023 files, the "region" mapping succeeded.
