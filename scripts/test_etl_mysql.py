#!/usr/bin/env python
"""
로컬 MySQL을 사용한 ETL 테스트 스크립트.

사용법:
    # 기본 설정 (root 계정, 비밀번호 없음)
    python -m scripts.test_etl_mysql

    # 비밀번호 있는 경우
    python -m scripts.test_etl_mysql --password yourpassword

    # 사용자 지정
    python -m scripts.test_etl_mysql --user myuser --password mypass --host 127.0.0.1 --port 3306

    # 기존 DB 사용 (테이블만 재생성)
    python -m scripts.test_etl_mysql --database beyondu_test
"""

import argparse
import sys
import io
from pathlib import Path
from urllib.parse import quote_plus

# Windows 콘솔 UTF-8 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

from src.extract.excel_reader import ExcelReader
from src.load.models import University, LanguageRequirement
from src.load.database import DatabaseLoader


def format_requirement_label(req: LanguageRequirement) -> str:
    """언어 요구 사항에 대한 사람이 읽을 수 있는 레이블을 생성합니다."""
    parts = [req.exam_type]
    if req.min_score is not None:
        # 점수가 정수이면 .0을 제거합니다.
        score = int(req.min_score) if req.min_score.is_integer() else req.min_score
        parts.append(str(score))
    if req.level_code:
        parts.append(f"({req.level_code})")
    return " ".join(parts)


def check_mysql_driver():
    """MySQL 드라이버 확인."""
    try:
        import pymysql
        return "pymysql"
    except ImportError:
        pass

    try:
        import mysql.connector
        return "mysql-connector-python"
    except ImportError:
        pass

    return None


def create_database_if_not_exists(
    user: str, password: str, host: str, port: int, database: str
):
    """데이터베이스가 없으면 생성."""
    driver = check_mysql_driver()
    # 비밀번호의 특수문자를 URL 인코딩
    encoded_password = quote_plus(password) if password else ""

    if driver == "pymysql":
        base_url = f"mysql+pymysql://{user}:{encoded_password}@{host}:{port}/"
    else:
        base_url = f"mysql+mysqlconnector://{user}:{encoded_password}@{host}:{port}/"

    engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    engine.dispose()
    print(f"  [OK] 데이터베이스 '{database}' 확인/생성 완료")


def main():
    parser = argparse.ArgumentParser(description="MySQL ETL 테스트")
    parser.add_argument("--user", "-u", default="root", help="MySQL 사용자 (기본: root)")
    parser.add_argument(
        "--password", "-p", default="", help="MySQL 비밀번호 (기본: 없음)"
    )
    parser.add_argument(
        "--host", "-H", default="localhost", help="MySQL 호스트 (기본: localhost)"
    )
    parser.add_argument("--port", "-P", type=int, default=3306, help="MySQL 포트 (기본: 3306)")
    parser.add_argument(
        "--database", "-d", default="beyondu_test", help="데이터베이스 이름 (기본: beyondu_test)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print(" BeyondU ETL - MySQL 테스트")
    print("=" * 70)

    # MySQL 드라이버 확인
    driver = check_mysql_driver()
    if not driver:
        print("\n[ERROR] MySQL 드라이버가 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요:")
        print("  pip install pymysql")
        print("  또는")
        print("  pip install mysql-connector-python")
        sys.exit(1)

    print(f"\n[INFO] MySQL 드라이버: {driver}")

    # 연결 URL 생성 (특수문자 URL 인코딩)
    encoded_password = quote_plus(args.password) if args.password else ""
    password_part = f":{encoded_password}" if args.password else ""

    if driver == "pymysql":
        database_url = f"mysql+pymysql://{args.user}{password_part}@{args.host}:{args.port}/{args.database}?charset=utf8mb4"
    else:
        database_url = f"mysql+mysqlconnector://{args.user}{password_part}@{args.host}:{args.port}/{args.database}?charset=utf8mb4"

    print(
        f"[INFO] 연결 URL: mysql://{args.user}:****@{args.host}:{args.port}/{args.database}"
    )

    # 데이터베이스 생성
    print(f"\n[1/5] 데이터베이스 설정...")
    try:
        create_database_if_not_exists(
            args.user, args.password, args.host, args.port, args.database
        )
    except Exception as e:
        print(f"\n[ERROR] MySQL 연결 실패: {e}")
        print("\nMySQL이 실행 중인지 확인하세요.")
        print("연결 정보가 올바른지 확인하세요.")
        sys.exit(1)

    # DatabaseLoader 초기화
    try:
        loader = DatabaseLoader(database_url=database_url)
    except Exception as e:
        print(f"\n[ERROR] DatabaseLoader 초기화 실패: {e}")
        sys.exit(1)

    # 테이블 생성
    print(f"\n[2/5] 테이블 초기화...")
    try:
        loader.drop_tables()
        loader.create_tables()
        print("  [OK] 테이블 생성 완료")
    except Exception as e:
        print(f"  [ERROR] 테이블 생성 실패: {e}")
        sys.exit(1)

    # 샘플 엑셀 파일 찾기
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    excel_files = list(data_dir.glob("*.xlsx"))

    if not excel_files:
        print("\n[ERROR] 엑셀 파일을 찾을 수 없습니다.")
        print(f"경로: {data_dir}")
        sys.exit(1)

    # 가장 최근 파일 사용 (2026-2학기 1차 우선)
    target_file = None
    for f in excel_files:
        if "2026-2" in f.name and "1차" in f.name:
            target_file = f
            break
    if not target_file:
        target_file = excel_files[0]

    print(f"\n[3/5] 엑셀 파일 읽기: {target_file.name}")

    # 엑셀 읽기
    try:
        reader = ExcelReader(target_file)
        df = reader.read()
        print(f"  [OK] 총 {len(df)}개 행 읽음")
    except Exception as e:
        print(f"  [ERROR] 엑셀 읽기 실패: {e}")
        sys.exit(1)

    # 데이터 로드
    print(f"\n[4/5] 데이터베이스 적재...")
    try:
        stats = loader.load_universities_dataframe(
            df
        )
        print(f"  [OK] 대학 삽입: {stats['inserted']}")
        print(f"  [OK] 대학 업데이트: {stats['updated']}")
        print(f"  [OK] 스킵: {stats['skipped']}")
        print(f"  [OK] 어학 요건 레코드: {stats['language_reqs']}")
    except Exception as e:
        print(f"  [ERROR] 데이터 적재 실패: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # 결과 확인
    print(f"\n[5/5] 결과 확인...")

    universities = loader.get_all_universities()
    requirements = loader.get_all_language_requirements()

    print(f"\n{'='*70}")
    print(f" DB 통계")
    print(f"{'='*70}")
    print(f"  총 대학 수: {len(universities)}")
    print(f"  총 어학 요건 레코드: {len(requirements)}")

    if universities:
        # 지역별 통계
        region_counts = {}
        for u in universities:
            region_counts[u.region] = region_counts.get(u.region, 0) + 1

        print(f"\n[지역별 대학 수]")
        for region, count in sorted(region_counts.items(), key=lambda x: -x[1])[:6]:
            if region:
                print(f"  {region}: {count}")

        # 국가별 통계 (상위 5개)
        country_counts = {}
        for u in universities:
            country_counts[u.nation] = country_counts.get(u.nation, 0) + 1

        print(f"\n[국가별 대학 수 (상위 5개)]")
        for country, count in sorted(country_counts.items(), key=lambda x: -x[1])[:5]:
            if country:
                print(f"  {country}: {count}")

    if requirements:
        # 시험 종류별 통계
        test_type_counts = {}
        for r in requirements:
            test_type_counts[r.exam_type] = test_type_counts.get(r.exam_type, 0) + 1

        print(f"\n[시험 종류별 요건 수]")
        for test_type, count in sorted(test_type_counts.items(), key=lambda x: -x[1]):
            print(f"  {test_type}: {count}")

    # 샘플 대학 상세 정보 출력
    print(f"\n{'='*70}")
    print(f" 샘플 대학 상세 (처음 3개)")
    print(f"{'='*70}")

    # 실제 대학 데이터만 필터링 (합계 행 제외)
    real_universities = [
        u for u in universities if u.serial_number and u.serial_number.startswith("E")
    ][:3]

    for u in real_universities:
        print(f"\n[{u.id}] {u.name_kor}")
        print(f"  일련번호: {u.serial_number}")

        program_types = []
        if u.is_exchange:
            program_types.append("교환")
        if u.is_visit:
            program_types.append("방문")
        program_str = ", ".join(program_types) if program_types else "N/A"
        print(f"  프로그램: {program_str}")
        
        print(f"  지역/국가: {u.region} / {u.nation}")
        print(f"  어학요건(원문): {u.language_requirement_text or '-'}")
        print(f"  최소학점: {u.min_gpa or '-'}")

        # 해당 대학의 어학 요건
        uni_reqs = [r for r in requirements if r.university_id == u.id]
        if uni_reqs:
            print(f"  파싱된 어학 요건 ({len(uni_reqs)}개):")
            for r in uni_reqs:
                label = format_requirement_label(r)
                print(f"    - {label} (group: {r.language_group or 'N/A'})")

    # MySQL 접속 방법 안내
    print(f"\n{'='*70}")
    print(f" 테스트 완료!")
    print(f"{'='*70}")
    print(f"\nMySQL Workbench 또는 CLI로 확인:")
    print(f"  mysql -u {args.user} -p -D {args.database}")
    print(f"\nSQL 쿼리 예시:")
    print(f"  SELECT * FROM university LIMIT 10;")
    print(f"  SELECT * FROM language_requirement WHERE university_id = 1;")
    print(f"  SELECT u.name_kor, u.nation, lr.exam_type, lr.min_score")
    print(f"    FROM university u")
    print(f"    JOIN language_requirement lr ON u.id = lr.university_id")
    print(f"    WHERE lr.exam_type = 'TOEFL_IBT' AND lr.min_score <= 80;")


if __name__ == "__main__":
    main()
