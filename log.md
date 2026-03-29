# BeyondU-Data ETL 구현 로그 (포트폴리오 정리)

## 1) 프로젝트 개요
- 목표: 매 학기 다른 형식으로 배포되는 교환학생 Excel 데이터를 정규화해 RDB(MySQL/SQLAlchemy)로 적재하는 Python ETL 파이프라인 구축
- 핵심 가치:
  - 반정형(엑셀) 데이터의 신뢰 가능한 구조화
  - 규칙 기반 파싱(어학/학점/후기) 자동화
  - 중복 방지 Upsert 및 운영 배포 자동화(CI/CD)

---

## 2) 아키텍처 및 실행 흐름
- 엔트리포인트: `scripts/run_etl.py`
- 흐름:
  1. **Extract**: `ExcelReader.read()`로 엑셀 원본 로딩 + 헤더 인식 + 컬럼 표준화
  2. **Transform**: `DataCleaner.clean()`으로 공백/병합셀/요약행/학점 포맷 정리
  3. **Load**: `DatabaseLoader.load_universities_dataframe()`으로 DB Upsert + 어학요건 분해 적재

- 실행 예시:
  - 전체 재구축: `python -m scripts.run_etl --drop-db --input data/raw`
  - 최신 파일만: `python -m scripts.run_etl --latest-only`

---

## 3) DB 스키마 (현재 모델 기준)
현재 스키마는 `src/load/models.py` 기준으로 `university`, `language_requirement` 중심이며, 포트폴리오 관점에서 아래처럼 컬럼/의미/키 제약을 정리할 수 있음.

### 3-1. university 테이블

| 컬럼명 | Type | 비고 (PK/FK/의미) |
|---|---|---|
| id | BIGINT | PK, Auto Increment, 대학 레코드 고유 식별자 |
| semester | VARCHAR(100) | 모집 학기. 현재는 다학기 값을 문자열로 누적 저장(예: `2025-2, 2025-1`) |
| region | VARCHAR(100) | 권역(유럽/북미/아시아 등) |
| nation | VARCHAR(100) | 국가명 |
| name_kor | VARCHAR(255) | 대학 한글명 |
| name_eng | VARCHAR(255) | 대학 영문명 |
| min_gpa | FLOAT | 지원 최소 학점 |
| significant_note | TEXT | 중요사항 원문 |
| remark | TEXT | 비고/참고사항 통합 텍스트 |
| available_majors | TEXT | 지원 가능 전공(원문 텍스트) |
| website_url | TEXT | 대학/국제처 관련 URL |
| badge | VARCHAR(100) | 기관 분류/배지 정보 |
| is_exchange | BOOLEAN | 교환학생 프로그램 가능 여부 |
| is_visit | BOOLEAN | 방문학생 프로그램 가능 여부 |
| has_review | BOOLEAN | 후기 존재 여부 |
| review_year | VARCHAR(50) | 후기 연도/연도범위(예: `2018`, `2013-2019`) |
| language_score | TEXT | 어학요건 원문 텍스트(파싱 전 원본 보존) |

인덱스:
- `idx_university_nation` (`nation`)
- `idx_university_region` (`region`)
- `idx_university_name_kor` (`name_kor`)

### 3-2. language_requirement 테이블

| 컬럼명 | Type | 비고 (PK/FK/의미) |
|---|---|---|
| id | BIGINT | PK, Auto Increment, 어학요건 레코드 식별자 |
| university_id | BIGINT | FK -> `university.id` (ON DELETE CASCADE), 대학 참조 |
| language_group | VARCHAR(50) | 언어 그룹(ENGLISH/JAPANESE/CHINESE 등) |
| exam_type | VARCHAR(50) | 시험 종류(TOEFL/IELTS/JLPT 등) |
| min_score | FLOAT | 최소 요구 점수 |
| level_code | VARCHAR(50), NULL | 등급 코드(A2, EU_B2 등) |
| is_available | BOOLEAN | 해당 시험 인정 가능 여부(제외 규칙 반영 결과) |

인덱스:
- `idx_lang_req_university_id` (`university_id`)
- `idx_lang_req_exam_type` (`exam_type`)

### 3-3. 스키마 진화 이력(커밋/마이그레이션 기반)
- PK 타입을 `INT -> BIGINT`로 확장 (`88c86c5`): 데이터 증가 대비
- 사용하지 않는 컬럼 제거 (`thumbnail_url`, `available_semester`) (`d1711e6` + alembic)
- `badge` 컬럼 도입 (`c31b6d0`): 기관 분류 정보 보강

### 3-4. 정규화 관점 진단 (현재 위반 포인트)

현재 스키마는 ETL 운영 효율에는 유리하지만, 조회/확장성 관점에서 일부 정규형 위반 또는 비정규 저장이 존재함.

1. 1NF(원자값) 위반 가능 지점
- `semester`: 다중 값(쉼표 구분) 누적 저장
- `review_year`: 단일 연도/범위 문자열 혼재
- `available_majors`, `remark`, `significant_note`, `language_score`: 구조화되지 않은 복합 텍스트

2. 3NF 관점의 이행/중복 의존 가능 지점
- `nation -> region`은 사실상 참조 관계인데 `university`에 중복 저장(갱신 이상 가능)
- `badge`가 기관 분류 코드라면 별도 도메인 테이블로 분리 가능
- `exam_type`, `language_group`, `level_code`는 코드성 속성으로 마스터 테이블 분리 여지 존재

3. 도메인 일관성 문제
- 문자열 코드(`review_year`, `semester`)는 정렬/필터링/집계 시 파싱 비용 증가
- 장문 텍스트 필드 중심 저장은 검색/통계 분석에 불리

### 3-5. 정규화 확장 방향 (권장 목표: 최소 3NF)

1. 학기 이력 분리 (가장 우선)
- 신규 테이블: `university_semester`
  - `id` PK
  - `university_id` FK
  - `year` SMALLINT
  - `term` VARCHAR(10) (`1`, `2`, `SUMMER`, `WINTER` 등)
  - Unique(`university_id`, `year`, `term`)
- 효과: 다학기 문자열 제거, 학기별 분석/정렬 정확도 향상

2. 지역/국가 정규화
- `region`(code/name), `nation`(code/name, region_code FK) 분리
- `university`는 `nation_code` FK만 보유하고 `region`은 조인으로 도출
- 효과: 국가/권역 변경 시 단일 지점 갱신, 데이터 일관성 강화

3. 후기 정보 구조화
- `university_review_meta` 또는 `review_snapshot` 테이블 분리
  - `has_review`, `start_year`, `end_year`로 분해
- 효과: 연도 범위 질의/통계 단순화

4. 전공/비고 텍스트의 점진적 구조화
- `major_catalog`, `university_major` 매핑 테이블 도입(장기)
- `remark`는 원문 보관(`raw_remark`) + 태그형 파생 테이블(`remark_tag`) 이원화
- 효과: full-text 의존도 완화, 조건 검색 품질 향상

5. 시험/언어 코드 마스터 분리
- `language_exam`(exam_type, language_group)
- `language_level_code`(level_code, 기준 설명)
- `language_requirement`는 FK 기반으로 참조
- 효과: 코드값 오타/불일치 방지, 규칙 관리 중앙화

### 3-6. 현실적인 마이그레이션 순서

1. `university_semester` 신설 후 ETL write path 이중화(기존 `semester`도 함께 유지)
2. API/조회 로직을 신규 테이블 사용으로 전환
3. 데이터 백필 완료 후 `university.semester` 제거
4. `nation/region` 참조 정규화 적용
5. 후기/전공/코드 마스터를 단계적으로 분리

이 순서를 따르면 서비스 중단 없이 점진적으로 1NF/3NF 위반 지점을 줄일 수 있음.
## 4) 구현 상세

### 4-1. Extract: `src/extract/excel_reader.py`
- 다양한 헤더 명칭을 `COLUMN_MAPPING`으로 표준 컬럼으로 매핑
  - 예: 국문/영문 혼재 헤더를 `nation`, `name_eng`, `language_requirement` 등으로 통일
- 헤더 행 자동 탐지(`_find_header_row`): 상단 10행에서 키워드 검색
- 중복 컬럼명 자동 disambiguation (`col`, `col_1`, ...)
- 병합셀 케이스를 전제한 데이터 로딩
- 2023 파일처럼 `region` 누락 시, 2024/2025 파일 참조 매핑으로 보정
- 파일명 메타 추출(`extract_file_metadata`): 학기 정보 파생

### 4-2. Transform: `src/transform/cleaner.py`
- 문자열 공백 정규화
- `program_type` 개행/공백 정리
- GPA 문자열 정규화
  - 숫자만 있으면 `x/4.5` 형태로 변환
- 병합셀 영향 컬럼(`nation`, `region`, `program_type`, `institution`) forward fill
- 필수값 없는 행/합계행 제거

### 4-3. Parse: `src/transform/parser.py`
- `LanguageParser`
  - 코드 기반 규칙(`A1`, `EU_B2`, `JP_C1` 등) + 직접 점수(`TOEFL 80`, `IELTS 6.5`) 혼합 파싱
  - 직접 점수가 있으면 코드 확장 결과를 override하는 전략
  - 제외 패턴(`TOEIC 제외`, `ITP 제외`) 처리
  - 선택사항(`없음`, `N/A`) 처리
- `GPAParser`: 텍스트에서 유효 수치 추출
- `WebsiteURLParser`: 프로토콜 없는 URL 보정
- `ReviewParser`: 후기 존재 여부/연도 범위 추출

### 4-4. Load: `src/load/database.py`
- 비즈니스 키: `(name_eng, nation)` 기준으로 Upsert
- 기존 대학 발견 시:
  - semester 누적 병합(중복 제거 + 정렬)
  - 나머지 필드 업데이트
- 신규 대학이면 insert
- 어학요건 적재:
  - 대학별 기존 `language_requirement` 삭제 후 재생성(동기화 방식)
  - 제외 시험/optional 규칙 반영
- region이 미분류면 nation 기반 보정 맵 적용

---

## 5) 테스트 전략
- `tests/test_extract.py`
  - 헤더 매핑/파일 미존재/병합셀 시나리오
- `tests/test_transform.py`
  - 공백 정리/무효 행 제거
- `tests/test_language_parser.py`
  - 코드 확장/직접점수/예외패턴/선택요건 등 파서 규칙 검증

추가로 `scripts/verify_*.py`, `scripts/check_db_*`, `scripts/inspect_*` 류의 운영 검증 스크립트가 존재하여 실제 적재 결과 수동 검증까지 지원.

---

## 6) 커밋 로그 기반 구현 과정 요약

### 단계 A. 초기 골격 구축
- `4a4f4b0`, `41e8b6d`, `c38fc3d`, `689bb69`
- 내용:
  - Extract/Transform/Load 기본 모듈 생성
  - 언어요건 파서 초안과 DB 적재 유틸 구축

### 단계 B. DB/모델 고도화
- `d64fc53`, `2d66eb1`, `90d4a89`, `c31b6d0`, `88c86c5`, `d1711e6`
- 내용:
  - 언어요건 구조 고도화 및 제외 규칙 반영
  - 모델 필드 정리(미사용 필드 삭제)
  - badge 필드 추가
  - PK BIGINT 전환
  - 스키마 경량화

### 단계 C. 엑셀 파싱 안정화
- `5b85b65`, `a545182`, `07149fa`, `2977f26`
- 내용:
  - 병합셀/헤더 변형 대응
  - 컬럼 매핑 정확도 개선
  - 데이터 파싱 오류 수정 반복

### 단계 D. 품질/운영 안정화
- `7a98d25`, `be00c3f`, `f4c3360`, `9bbf927`, `17f790a`, `13e3b69`
- 내용:
  - ruff/mypy/pytest 중심 안정화
  - 타입 추론 이슈 수정
  - 테스트 실패 및 경계 케이스 지속 보수

### 단계 E. 운영 자동화
- `945f2cf` 및 배포 워크플로우 관련 chore 커밋들
- 내용:
  - EC2 대상 마이그레이션/초기화/동기화 자동화
  - S3 동기화 스크립트 도입

---

## 7) 트러블슈팅 기록 (포트폴리오용)

### 이슈 1) 엑셀 헤더가 매 학기 바뀌어 파싱 실패
- 증상:
  - 컬럼명이 고정되지 않아 ETL이 필수 필드를 놓침
- 원인:
  - 실무 문서 특성상 같은 의미의 헤더가 여러 표현으로 존재
- 대응:
  - `COLUMN_MAPPING` 다중 동의어 사전 구축
  - 헤더 자동 탐지 로직 도입
  - 테스트에서 매핑 회귀 검증 강화 (`2977f26`, `13e3b69`)
- 결과:
  - 신규 양식 유입 시에도 코드 변경량 최소화

### 이슈 2) 병합셀로 인한 행 단위 데이터 유실
- 증상:
  - nation/region/program_type가 일부 행에서 NaN
- 대응:
  - Transform 단계에서 컬럼 선택적 `ffill` 적용
  - 전역 `ffill`은 부작용(GPA 오염)으로 제거
- 결과:
  - 구조 컬럼만 안정 복구, 수치 컬럼 오염 방지

### 이슈 3) 어학요건 텍스트가 코드/점수 혼재
- 증상:
  - `A2`, `TOEFL 80`, `TOEIC 제외` 등이 혼합된 문자열 처리 어려움
- 대응:
  - 코드 확장 + 직접점수 override 2단계 파싱 전략
  - excluded/optional 패턴 별도 처리
  - 파서 테스트 케이스 다수 추가
- 결과:
  - 검색 가능한 정규화 점수 테이블 생성 가능

### 이슈 4) 스키마 불일치로 ETL 로드 실패
- 증상:
  - 모델에는 없는 컬럼(`available_semester`, `thumbnail_url`)이 적재 데이터에 포함
- 대응:
  - 미사용 컬럼 제거 마이그레이션 (`d1711e6`)
  - 로더 방어 코드로 잔여 키 제거
- 결과:
  - 모델/적재 로직 정합성 확보

### 이슈 5) PK 확장 필요
- 증상:
  - 데이터 누적 대비 `INT` PK 한계 우려
- 대응:
  - PK를 BIGINT로 전환 (`88c86c5`)
- 결과:
  - 장기 운영 확장성 확보

### 이슈 6) 정적분석/테스트 지속 실패
- 증상:
  - lint/mypy/pytest 경고 및 실패 반복
- 대응:
  - 타입 힌트/추론 보정, 테스트 케이스 수정, 반복적인 CI 안정화 커밋
- 결과:
  - 코드 품질 게이트 통과 가능 수준으로 수렴

---

## 8) 내가 이 프로젝트에서 강조할 수 있는 역량
- 반정형 데이터 정규화 설계 역량
- 규칙 기반 파서 설계 및 예외 처리 능력
- SQLAlchemy 모델링 + Upsert/관계형 적재 구현 능력
- 테스트/린트/타입체크 기반 품질 관리
- 배포 파이프라인(EC2/S3/마이그레이션) 운영 자동화 경험

---

## 9) 포트폴리오에 넣기 좋은 성과 문장 예시
- “학기별로 포맷이 달라지는 교환학생 Excel 원본을 자동 정규화하여, 검색 가능한 RDB 스키마(`university`, `language_requirement`)로 일관 적재하는 ETL을 설계/구현했다.”
- “어학요건 텍스트를 코드 확장 + 직접점수 override 방식으로 파싱해, 단순 문자열 저장이 아닌 정량 필터링 가능한 점수 데이터셋으로 전환했다.”
- “PK BIGINT 전환, 미사용 컬럼 제거, 타입/린트/테스트 안정화를 통해 운영 가능성을 높이고, 배포 워크플로우까지 자동화했다.”

