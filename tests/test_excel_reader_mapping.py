
from src.extract.excel_reader import ExcelReader

try:
    print("COLUMN_MAPPING keys:", list(ExcelReader.COLUMN_MAPPING.keys()))
    print("COLUMN_MAPPING:", ExcelReader.COLUMN_MAPPING)
except AttributeError:
    print("ExcelReader has no COLUMN_MAPPING attribute")
except Exception as e:
    print(f"Error: {e}")
