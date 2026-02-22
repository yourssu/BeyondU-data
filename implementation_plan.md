# Fixing Failing Tests Implementation Plan

## 1. Goal Description
The recent changes to `LANGUAGE_STANDARDS` and the `ExcelReader` class have broken some existing tests in `test_extract.py` and `test_language_parser.py`. The goal is to update these tests to match the new desired behaviors.

1. **`test_extract.py`**: The `ExcelReader` was refactored significantly to remove global forward filling (`ffill()`) for merged cells. That responsibility was intentionally moved to `DataCleaner`. Therefore, `test_read_merged_cells` is no longer a valid test for `ExcelReader` and will be updated to expect `NaN` for merged cells, or removed.
2. **`test_language_parser.py`**: The regional codes for Chinese and Japanese changed from `B1~B3` to `CN_B1~CN_B3` and `C1~C2` to `JP_C1~JP_C2`. The assertions in `test_chinese_codes_exist`, `test_japanese_codes_exist`, and `test_parse_b1_chinese` still expect the old keys. These will be updated.

## 2. Proposed Changes

### 2.1 Update `tests/test_extract.py`
- Modify `test_read_merged_cells` so it correctly asserts that the second row's `nation` value for a merged cell is `nan` (or technically `None` / `float('nan')`), demonstrating that `ExcelReader` is no longer incorrectly forward-filling data, which is now handled downstream.

### 2.2 Update `tests/test_language_parser.py`
- Modify `test_chinese_codes_exist` to loop over `["CN_B1", "CN_B2", "CN_B3"]`.
- Modify `test_japanese_codes_exist` to loop over `["JP_C1", "JP_C2"]`.
- Modify `test_parse_b1_chinese` to assert `level_code == "CN_B1"` instead of `"B1"`.

## 3. Verification Plan
- **Automated Tests**:
    - Run `python -m pytest tests/ -v`
    - All tests should pass without any `AssertionError`.
