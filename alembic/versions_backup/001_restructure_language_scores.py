"""Restructure language_scores table for code-based parsing.

Revision ID: 001_restructure_language_scores
Revises:
Create Date: 2025-01-30

Changes:
- Add university_id (FK to universities)
- Change score (String) -> min_score (Float) for numeric comparison
- Add standard_code column for tracking code-based inputs (A2, B1, etc.)
- Add created_at timestamp
- Add indexes for search optimization
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_restructure_language_scores"
down_revision = "002_restructure_universities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: 새로운 language_scores 테이블 구조로 변경

    기존 테이블 구조:
        - score_id (PK)
        - test_type (String)
        - score (String)

    새 테이블 구조:
        - score_id (PK, BigInteger, autoincrement)
        - university_id (FK -> universities.university_id)
        - test_type (String(20))
        - min_score (Float) - 숫자 비교 연산용
        - standard_code (String(10), nullable) - 등급 코드 (A2, B1 등)
        - created_at (DateTime)
    """
    # 1. 기존 테이블 삭제 (데이터가 있다면 백업 필요)
    op.drop_table("language_scores", if_exists=True)

    # 2. 새 테이블 생성
    op.create_table(
        "language_scores",
        sa.Column("score_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("university_id", sa.BigInteger(), nullable=False),
        sa.Column("test_type", sa.String(20), nullable=False, comment="시험 종류 (TOEFL_IBT, IELTS, TOEIC 등)"),
        sa.Column("min_score", sa.Float(), nullable=False, comment="최소 점수 (숫자 비교용)"),
        sa.Column("standard_code", sa.String(10), nullable=True, comment="등급 코드 (A2, B1 등 - 코드형 입력인 경우)"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("score_id"),
        sa.ForeignKeyConstraint(
            ["university_id"],
            ["university.id"],
            ondelete="CASCADE",
        ),
    )

    # 3. 인덱스 생성
    op.create_index("idx_language_score_test_type", "language_scores", ["test_type"])
    op.create_index("idx_language_score_university", "language_scores", ["university_id"])
    op.create_index("idx_language_score_min_score", "language_scores", ["min_score"])
    op.create_index("idx_language_score_uni_test", "language_scores", ["university_id", "test_type"])


def downgrade() -> None:
    """
    Downgrade: 이전 language_scores 테이블 구조로 복원

    주의: 새 구조의 데이터는 손실됨
    """
    # 1. 새 테이블 삭제
    op.drop_index("idx_language_score_uni_test", table_name="language_scores")
    op.drop_index("idx_language_score_min_score", table_name="language_scores")
    op.drop_index("idx_language_score_university", table_name="language_scores")
    op.drop_index("idx_language_score_test_type", table_name="language_scores")
    op.drop_table("language_scores", if_exists=True)

    # 2. 기존 테이블 복원
    op.create_table(
        "language_scores",
        sa.Column("score_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("test_type", sa.String(20), nullable=False, comment="시험 종류 (TOEIC, TOEFL, IELTS 등)"),
        sa.Column("score", sa.String(20), nullable=False, comment="취득 점수 또는 등급"),
        sa.PrimaryKeyConstraint("score_id"),
    )
    op.create_index("idx_language_score_test_type", "language_scores", ["test_type"])
