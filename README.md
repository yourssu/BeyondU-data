# BeyondU-Data-Engine: 교환학생 데이터 ETL 파이프라인

## 1. 프로젝트 개요

본 프로젝트는 여러 엑셀 파일 형태로 흩어져 있는 대학교 교환학생 프로그램을 취합하여, 정제되고 구조화된 데이터베이스로 구축하는 ETL(Extract, Transform, Load) 파이프라인입니다. 이 시스템을 통해 비정형적인 엑셀 데이터를 검색 및 활용이 용이한 형태로 변환할 수 있습니다.

## 2. 기술 스택

- **언어**: Python 3.11+
- **데이터 처리**: Pandas, Openpyxl
- **데이터베이스 ORM**: SQLAlchemy
- **데이터베이스**: MySQL (또는 설정에 따라 다른 DB로 변경 가능)
- **DB 마이그레이션**: Alembic
- **설정 관리**: Pydantic

## 3. 실행 방법

### 3.1. 환경 설정

1.  **필요 라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

2.  **데이터베이스 연결 설정**
    - 프로젝트 루트 디렉토리에 `.env` 파일을 생성합니다.
    - 아래와 같이 `DATABASE_URL`을 설정합니다. (사용자, 비밀번호, 호스트, DB명은 실제 환경에 맞게 수정)
    ```
    DATABASE_URL=mysql+mysqlconnector://<user>:<password>@<host>/<dbname>?charset=utf8mb4
    ```
    - 예시: `DATABASE_URL=mysql+mysqlconnector://root:password@127.0.0.1:3306/beyondu_test?charset=utf8mb4`

### 3.2. ETL 파이프라인 실행

- 아래 명령어를 실행하면 `data/raw` 폴더의 모든 엑셀 파일을 읽어 ETL을 수행합니다.
- `--drop-db` 옵션은 기존 테이블을 모두 삭제하고 새로 생성하므로, 매번 깨끗한 상태에서 데이터를 구축할 수 있습니다.

```bash
python -m scripts.run_etl --drop-db --input data/raw
```

## 4. 디렉토리 구조 및 파일 역할

```
.
├── .env                  # DB 연결 정보 등 민감한 환경 변수 설정
├── alembic/              # Alembic DB 마이그레이션 관리
├── data/
│   ├── raw/              # 원본 엑셀 파일 저장 위치
│   └── processed/        # (선택) 가공된 데이터 저장 위치
├── scripts/
│   ├── run_etl.py        # 메인 ETL 파이프라인 실행 스크립트
│   └── ...               # 기타 보조 스크립트
├── src/
│   ├── extract/
│   │   └── excel_reader.py # 엑셀 파일 데이터 추출 및 1차 정제
│   ├── transform/
│   │   └── parser.py       # 어학성적, GPA, 웹사이트 등 텍스트 파싱
│   ├── load/
│   │   ├── models.py     # SQLAlchemy DB 모델(테이블) 정의
│   │   └── database.py   # 데이터베이스 연결 및 데이터 적재(Upsert)
│   └── config.py           # Pydantic을 이용한 프로젝트 설정 관리
└── README.md               # 프로젝트 설명서
```

## 5. ETL 파이프라인 상세

### 5.1. Extract (추출)

- **담당**: `src/extract/excel_reader.py`의 `ExcelReader` 클래스
- **주요 기능**:
    - 다양한 양식의 엑셀 파일(`.xlsx`, `.xls`)을 읽어들입니다.
    - 병합된 셀을 자동으로 인식하고 값을 채워 데이터 유실을 방지합니다.
    - `COLUMN_MAPPING`을 통해 한글 컬럼명을 표준 영문명으로 정규화합니다.
    - '참고사항', '유의사항', '비고', '특이사항' 등 여러 이름의 컬럼을 `remark`라는 단일 필드로 통합하기 위해 모두 동일한 이름으로 매핑합니다. 이후 중복된 컬럼명의 내용은 하나의 필드로 병합됩니다.
    - `settings.excluded_institutions`에 정의된 기관(예: SAF, ACUCA)에 해당하는 데이터를 필터링하여 제외시킵니다.
    - '합계', '대학명' 등 불필요한 요약 및 헤더 행을 제거하여 순수 데이터만 추출합니다.

### 5.2. Transform (변환)

- **담당**: `src/transform/parser.py`의 파서 클래스들
- **주요 기능**:
    - **`LanguageParser`**: 가장 복잡한 '어학성적' 텍스트를 파싱하여 구조화된 데이터로 변환합니다.
        - **(규칙)** 명시된 점수 우선: `A-4 
 IELTS 6.5` 와 같이 표준 코드와 개별 점수가 혼합된 경우, 명시된 `IELTS 6.5`를 우선 적용하고, `A-4` 표준에만 있는 다른 시험(TOEIC 등)은 보충적으로 추가합니다.
        - **(규칙)** `
` 또는 공백으로 분리된 여러 개의 어학 요건을 모두 인식하여 별개의 레코드로 생성합니다.
        - **(규칙)** 지역별 기준 적용: '유럽' 지역 대학의 '영어 B2' 요건은 'EU_B2' 코드로 변환하여 처리합니다.
        - **(규칙)** `TOEFL(iBT)` 등 다양한 시험명 표기를 `TOEFL`과 같이 표준화된 `exam_type`으로 통일합니다.
    - **`WebsiteURLParser`**: `http://` 프로토콜이 없거나 `www`로 시작하는 등 비정형적인 웹사이트 주소를 인식하여 완전한 URL로 변환합니다.
    - **`GPAParser`**: `3.5/4.5`와 같은 텍스트에서 GPA 점수를 추출합니다.

### 5.3. Load (적재)

- **담당**: `src/load/database.py`의 `DatabaseLoader` 클래스
- **주요 기능**:
    - **Upsert 전략**: `(영문 대학명, 국가)` 조합을 비즈니스 키로 사용하여, 기존에 등록된 대학인지 판단합니다.
        - **기존 대학**: 새로운 학기 정보를 `semester` 필드에 누적하여 기록합니다. (예: "2024-1" -> "2024-2, 2024-1")
        - **신규 대학**: 새로운 레코드로 데이터베이스에 삽입합니다.
    - **Region 자동 매핑**: `region` 필드가 '미분류'일 경우, `nation` 필드(국가)를 기준으로 '북미', '유럽', '아시아' 등 올바른 지역을 자동으로 매핑합니다.
    - 변환된 데이터를 `university`와 `language_requirement` 테이블에 최종적으로 저장합니다.

## 6. 데이터베이스 스키마

### `university` 테이블

| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | Integer | **PK**, Auto-increment | 레코드의 고유 식별자 |
| `semester` | String | Not Null | 모집 학기 정보. "2024-2, 2024-1"과 같이 누적 기록됨. |
| `region` | String | Not Null | 지역(대륙). '미분류' 시 국가 정보로 자동 매핑됨. |
| `nation` | String | Not Null | 국가 |
| `name_kor` | String | Not Null | 대학명 (한글) |
| `name_eng` | String | Not Null | 대학명 (영문) |
| `min_gpa` | Float | Not Null | 최소 지원 학점 |
| `remark` | Text | Not Null | 주요 설명 필드. 엑셀의 '특이사항', '참고사항', '유의사항', '비고' 컬럼 내용이 모두 통합되어 저장됨. |
| `available_majors` | Text | Nullable | 지원 가능 전공 |
| `website_url` | Text | Nullable | 대학 공식 웹사이트 주소. 비정형 URL도 파싱하여 저장. |
| `is_exchange` | Boolean | Not Null | 교환학생 프로그램 여부 |
| `is_visit` | Boolean | Not Null | 방문학생 프로그램 여부 |
| `significant_note` | Text | Nullable | (사용되지 않음) 레거시 필드 |
| `thumbnail_url` | Text | Nullable | (미사용) 썸네일 이미지 URL |
| `available_semester` | String | Nullable | (미사용) 파견 가능 학기 |

### `language_requirement` 테이블

| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | Integer | **PK**, Auto-increment | 레코드의 고유 식별자 |
| `university_id` | Integer | **FK** (university.id) | `university` 테이블 외래 키 |
| `language_group` | String | Not Null | 언어 그룹 (예: "ENGLISH", "JAPANESE") |
| `exam_type` | String | Not Null | 시험 종류 (예: "TOEFL", "IELTS") |
| `min_score` | Float | Not Null | 최소 요구 점수 |
| `level_code` | String | Nullable | 표준 어학 기준 코드 (예: "A-4", "EU_B2") |
