import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extract.excel_reader import ExcelReader

def main():
    file_path = Path('data/raw/2026-2 교환학생 파견가능대학 및 지원자격(1차).xlsx')
    reader = ExcelReader(file_path)
    
    from openpyxl import load_workbook
    wb = load_workbook(file_path, data_only=True)
    sheet = wb.active

    data = []
    for row in sheet.rows:
        row_data = []
        for cell in row:
            row_data.append(cell.value)
        data.append(row_data)

    header_idx = reader._find_header_row(data)
    with open('headers.json', 'w', encoding='utf-8') as f:
        json.dump({"idx": header_idx, "data": data[header_idx] if header_idx is not None else []}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
