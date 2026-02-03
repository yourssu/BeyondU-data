#!/usr/bin/env python
"""
로컬 SQLite를 사용한 ETL 테스트 스크립트.
Docker 없이 빠르게 테스트할 수 있음.

사용법:
    python -m scripts.test_etl_local
"""

import sys
import io
from pathlib import Path

# Windows 콘솔 UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.extract.excel_reader import ExcelReader
from src.load.models import Base, LanguageScore, University
from src.load.database import DatabaseLoader
from src.transform.parser import LanguageParser, get_score_label


def main():
    # SQLite 데이터베이스 설정 (메모리 또는 파일)
    db_path = Path(__file__).parent.parent / "data" / "test_beyondu.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database_url = f"sqlite:///{db_path}"
    print(f"=== SQLite 테스트 DB 사용: {db_path} ===\n")

    # DatabaseLoader 초기화
    loader = DatabaseLoader(database_url=database_url)

    # 테이블 생성 (기존 테이블 삭제 후 재생성)
    print("[1/4] 테이블 초기화 중...")
    loader.drop_tables()
    loader.create_tables()
    print("  [OK] 테이블 생성 완료\n")

    # 샘플 엑셀 파일 찾기
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    excel_files = list(data_dir.glob("*.xlsx"))

    if not excel_files:
        print("[ERROR] 엑셀 파일을 찾을 수 없습니다.")
        return

    # 가장 최근 파일 사용 (2026-2학기 1차)
    target_file = None
    for f in excel_files:
        if "2026-2" in f.name and "1차" in f.name:
            target_file = f
            break

    if not target_file:
        target_file = excel_files[0]

    print(f"[2/4] 엑셀 파일 읽기: {target_file.name}")

    # 엑셀 읽기
    reader = ExcelReader(target_file)
    df = reader.read()
    metadata = reader.extract_file_metadata()

    print(f"  [OK] 총 {len(df)}개 행 읽음")
    print(f"  [OK] 컬럼: {list(df.columns)[:8]}...\n")

    # 데이터 로드
    print("[3/4] 데이터베이스 적재 중...")
    stats = loader.load_universities_dataframe(
        df,
        source_file=target_file.name,
    )

    print(f"  [OK] 대학 삽입: {stats['inserted']}")
    print(f"  [OK] 대학 업데이트: {stats['updated']}")
    print(f"  [OK] 스킵: {stats['skipped']}")
    print(f"  [OK] 어학 점수 레코드: {stats['language_scores']}\n")

    # 결과 확인
    print("[4/4] 결과 확인...\n")

    universities = loader.get_all_universities()
    scores = loader.get_all_language_scores()

    print(f"{'='*70}")
    print(f" DB 통계")
    print(f"{'='*70}")
    print(f"  총 대학 수: {len(universities)}")
    print(f"  총 어학 점수 레코드: {len(scores)}")

    if universities:
        # 지역별 통계
        region_counts = {}
        for u in universities:
            region_counts[u.region] = region_counts.get(u.region, 0) + 1

        print(f"\n[지역별 대학 수]")
        for region, count in sorted(region_counts.items(), key=lambda x: -x[1]):
            print(f"  {region}: {count}")

        # 국가별 통계 (상위 5개)
        country_counts = {}
        for u in universities:
            country_counts[u.country] = country_counts.get(u.country, 0) + 1

        print(f"\n[국가별 대학 수 (상위 5개)]")
        for country, count in sorted(country_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"  {country}: {count}")

    if scores:
        # 시험 종류별 통계
        test_type_counts = {}
        for s in scores:
            test_type_counts[s.test_type] = test_type_counts.get(s.test_type, 0) + 1

        print(f"\n[시험 종류별 레코드 수]")
        for test_type, count in sorted(test_type_counts.items(), key=lambda x: -x[1]):
            print(f"  {test_type}: {count}")

        # 등급 코드별 통계
        code_counts = {}
        for s in scores:
            code = s.standard_code or "직접입력"
            code_counts[code] = code_counts.get(code, 0) + 1

        print(f"\n[등급 코드별 레코드 수]")
        for code, count in sorted(code_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {code}: {count}")

    # 샘플 대학 상세 정보 출력
    print(f"\n{'='*70}")
    print(f" 샘플 대학 상세 정보 (처음 3개)")
    print(f"{'='*70}")

    for u in universities[:3]:
        print(f"\n[{u.university_id}] {u.name_kr}")
        print(f"  일련번호: {u.serial_number}")
        print(f"  프로그램: {u.program_type}")
        print(f"  지역/국가: {u.region} / {u.country}")
        print(f"  어학요건(원문): {u.language_requirement or '-'}")
        print(f"  최소학점: {u.min_gpa or '-'}")

        # 해당 대학의 어학 점수
        uni_scores = [s for s in scores if s.university_id == u.university_id]
        if uni_scores:
            print(f"  어학 점수 ({len(uni_scores)}개):")
            for s in uni_scores:
                label = get_score_label(s.test_type, s.min_score)
                print(f"    - {label} (code: {s.standard_code or '직접'})")

    print(f"\n{'='*70}")
    print(f" 테스트 완료!")
    print(f" DB 파일: {db_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
