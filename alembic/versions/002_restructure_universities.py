"""Restructure universities table.

Revision ID: 002_restructure_universities
Revises: 001_restructure_language_scores
Create Date: 2025-01-30

Changes:
- Simplify universities table to core fields
- Add BigInteger for university_id with autoincrement
- Make program_type, region NOT NULL
- Rename notes -> note (singular)
- Remove deprecated columns (institution, factsheet, student_review, etc.)
- Add name_kr index for search optimization
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_restructure_universities"
down_revision = "001_restructure_language_scores"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: 새로운 universities 테이블 구조로 변경

    새 테이블 구조:
        - university_id (BIGINT, PK, autoincrement)
        - serial_number (VARCHAR(20), unique) - 엑셀 일련번호
        - program_type (VARCHAR(50), NOT NULL) - 프로그램 구분
        - region (VARCHAR(50), NOT NULL) - 지역
        - country (VARCHAR(50), NOT NULL) - 국가
        - name_kr (VARCHAR(255), NOT NULL) - 대학명(국문)
        - name_en (VARCHAR(255)) - 대학명(영문)
        - department_info (TEXT) - 수학가능학과
        - website_url (TEXT) - 웹사이트
        - note (TEXT) - 특이사항/비고
        - language_requirement (TEXT) - 어학 요건 원문
        - min_gpa (VARCHAR(50)) - 최소 학점
        - source_file (VARCHAR(255)) - 출처 파일명
        - created_at (TIMESTAMP)
        - updated_at (TIMESTAMP)
    """
    # language_scores 테이블의 FK 제약조건 임시 제거
    op.drop_constraint(
        "language_scores_university_id_fkey",
        "language_scores",
        type_="foreignkey"
    )

    # 기존 테이블 삭제
    op.drop_table("universities")

    # 새 테이블 생성
    op.create_table(
        "universities",
        # Primary Key
        sa.Column(
            "university_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="시스템 내부 고유 식별자 (자동 증가)",
        ),
        # Serial Number (Unique)
        sa.Column(
            "serial_number",
            sa.String(20),
            unique=True,
            nullable=True,
            comment="국제처 엑셀 파일 내 고유 번호 (예: E0011)",
        ),
        # Program Type (NOT NULL)
        sa.Column(
            "program_type",
            sa.String(50),
            nullable=False,
            comment="교환학생 프로그램 성격 (일반교환, 방문교환 등)",
        ),
        # Region (NOT NULL)
        sa.Column(
            "region",
            sa.String(50),
            nullable=False,
            comment="파견 대학이 위치한 대륙별 지역 (유럽, 북미, 아시아 등)",
        ),
        # Country (NOT NULL)
        sa.Column(
            "country",
            sa.String(50),
            nullable=False,
            comment="파견 대학의 국가명",
        ),
        # University Names
        sa.Column(
            "name_kr",
            sa.String(255),
            nullable=False,
            comment="대학의 공식 국문 명칭",
        ),
        sa.Column(
            "name_en",
            sa.String(255),
            nullable=True,
            comment="대학의 공식 영문 명칭",
        ),
        # Department Info
        sa.Column(
            "department_info",
            sa.Text(),
            nullable=True,
            comment="파견 대학에서 지원 가능한 학과나 영어 강의 목록",
        ),
        # Website URL
        sa.Column(
            "website_url",
            sa.Text(),
            nullable=True,
            comment="상대교의 공식 홈페이지나 국제교류처 링크",
        ),
        # Note (unified from multiple fields)
        sa.Column(
            "note",
            sa.Text(),
            nullable=True,
            comment="비고란 및 지원 시 참고해야 할 주의사항",
        ),
        # Language Requirement (for parsing)
        sa.Column(
            "language_requirement",
            sa.Text(),
            nullable=True,
            comment="어학 성적 요건 원본 텍스트 (예: A2, TOEFL 80)",
        ),
        # Min GPA
        sa.Column(
            "min_gpa",
            sa.String(50),
            nullable=True,
            comment="최소 학점 요건 (예: 3.0/4.5)",
        ),
        # Metadata
        sa.Column(
            "source_file",
            sa.String(255),
            nullable=True,
            comment="데이터 출처 엑셀 파일명",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="레코드 생성 시각",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment="레코드 최종 수정 시각",
        ),
        # Constraints
        sa.PrimaryKeyConstraint("university_id"),
        sa.UniqueConstraint("serial_number"),
    )

    # 인덱스 생성
    op.create_index("idx_university_country", "universities", ["country"])
    op.create_index("idx_university_region", "universities", ["region"])
    op.create_index("idx_university_program", "universities", ["program_type"])
    op.create_index("idx_university_serial", "universities", ["serial_number"])
    op.create_index("idx_university_name_kr", "universities", ["name_kr"])

    # language_scores FK 제약조건 재생성
    op.create_foreign_key(
        "language_scores_university_id_fkey",
        "language_scores",
        "universities",
        ["university_id"],
        ["university_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """
    Downgrade: 이전 universities 테이블 구조로 복원

    주의: 새 구조의 데이터는 손실될 수 있음
    """
    # FK 제약조건 임시 제거
    op.drop_constraint(
        "language_scores_university_id_fkey",
        "language_scores",
        type_="foreignkey"
    )

    # 새 테이블 삭제
    op.drop_index("idx_university_name_kr", table_name="universities")
    op.drop_index("idx_university_serial", table_name="universities")
    op.drop_index("idx_university_program", table_name="universities")
    op.drop_index("idx_university_region", table_name="universities")
    op.drop_index("idx_university_country", table_name="universities")
    op.drop_table("universities")

    # 기존 테이블 복원
    op.create_table(
        "universities",
        sa.Column("university_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("serial_number", sa.String(20), unique=True, nullable=True),
        sa.Column("program_type", sa.String(50), nullable=True),
        sa.Column("institution", sa.String(50), nullable=True),
        sa.Column("region", sa.String(50), nullable=True),
        sa.Column("country", sa.String(50), nullable=False),
        sa.Column("name_kr", sa.String(255), nullable=False),
        sa.Column("name_en", sa.String(255), nullable=True),
        sa.Column("min_gpa", sa.String(50), nullable=True),
        sa.Column("language_requirement", sa.Text(), nullable=True),
        sa.Column("language_notes", sa.Text(), nullable=True),
        sa.Column("reference_info", sa.Text(), nullable=True),
        sa.Column("department_info", sa.Text(), nullable=True),
        sa.Column("factsheet", sa.String(100), nullable=True),
        sa.Column("student_review", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("website_url", sa.Text(), nullable=True),
        sa.Column("source_file", sa.String(255), nullable=True),
        sa.Column("semester", sa.String(20), nullable=True),
        sa.Column("recruitment_round", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("university_id"),
    )
    op.create_index("idx_university_country", "universities", ["country"])
    op.create_index("idx_university_region", "universities", ["region"])
    op.create_index("idx_university_program", "universities", ["program_type"])
    op.create_index("idx_university_serial", "universities", ["serial_number"])

    # FK 재생성
    op.create_foreign_key(
        "language_scores_university_id_fkey",
        "language_scores",
        "universities",
        ["university_id"],
        ["university_id"],
        ondelete="CASCADE",
    )
