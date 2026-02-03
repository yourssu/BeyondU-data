# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BeyondU-Data-Engine은 대학교 국제처 교환학생 엑셀 데이터를 ETL(Extract-Transform-Load) 패턴으로 처리하여 검색 가능한 데이터베이스로 변환하는 시스템입니다.

## Tech Stack

- **Language**: Python 3.11+
- **Data Processing**: Pandas, Openpyxl
- **Database**: AWS RDS
- **Cloud**: AWS S3 (원본 엑셀), AWS RDS (가공 데이터)
- **Infrastructure**: Docker, GitHub Actions

## Build & Run Commands

```bash
# 의존성 설치
pip install -r requirements.txt

# 로컬 PostgreSQL 실행 (Docker)
docker-compose up -d db

# DB 테이블 초기화
python -m scripts.run_etl --init-db

# 전체 ETL 파이프라인 실행
python -m scripts.run_etl --input data/raw/

# 단일 엑셀 파일 처리
python -m scripts.run_etl --file data/raw/2024_1차모집.xlsx

# Dry-run (DB 적재 없이 테스트)
python -m scripts.run_etl --file data/raw/sample.xlsx --dry-run

# CSV로 내보내기 (검증용)
python -m scripts.export_csv data/raw/sample.xlsx

# 테스트 실행
pytest tests/

# 단일 테스트 실행
pytest tests/test_transform.py::TestRequirementParser::test_parse_gpa_with_scale -v

# 린트
ruff check src/ tests/

# 타입 체크
mypy src/

# DB 마이그레이션 생성
alembic revision --autogenerate -m "description"

# DB 마이그레이션 적용
alembic upgrade head
```

## Architecture

### ETL Pipeline Flow

1. **Extract** (`src/extract/`)
   - `ExcelReader`: 병합 셀을 해제하고 원본 데이터 추출
   - 여러 버전의 엑셀 파일(1차, 2차 모집 등) 처리

2. **Transform** (`src/transform/`)
   - `DataCleaner`: 컬럼명 정규화, 병합 셀 forward-fill, 공백 정리
   - `RequirementParser`: 텍스트 조건을 구조화된 데이터로 파싱
     - "TOEFL IBT 100" → `{test_type: "TOEFL_IBT", min_score: 100}`
     - "3.5/4.5" → `{min_gpa: 3.5, max_scale: 4.5}`
     - "어학 성적 없음 선택 가능" → `{is_optional: true}`

3. **Load** (`src/load/`)
   - `DatabaseLoader`: Upsert 로직으로 중복 대학/모집차수 처리
   - `models.py`: University, Requirement 테이블 정의

### Database Schema

- **University**: id, name, country, region, link
- **Requirement**: university_id, recruitment_round, quota, language_*, gpa_*, notes
- 인덱스: gpa_min, language_test_type, recruitment_round (검색 최적화)

### Key Patterns

- 컬럼 매핑: 한글 컬럼명 → 영문 (`src/transform/cleaner.py:COLUMN_MAPPING`)
- 파일명에서 모집차수 추출: `2024_1차모집.xlsx` → "1차"
- GPA 정규화: 다른 스케일(4.0, 4.3, 4.5)을 통일 비교
