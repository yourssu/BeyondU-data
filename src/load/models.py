"""SQLAlchemy models for university exchange program data."""

from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class LanguageRequirement(Base):
    """
    대학별 어학 성적 요구사항 테이블.
    """

    __tablename__ = "language_requirement"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="어학 요구사항 고유 식별자"
    )
    university_id: Mapped[int] = mapped_column(
        ForeignKey("university.id", ondelete="CASCADE"),
        nullable=False, comment="대학교 ID"
    )
    language_group: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="언어권 분류 (ENGLISH, JAPANESE 등)"
    )
    exam_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="시험 종류 (TOEFL, IELTS, JLPT 등)"
    )
    min_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="요구되는 최소 점수"
    )
    level_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="레벨/등급 (예: B2, N2 등)"
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="해당 시험 인정 여부"
    )

    # Relationships
    university: Mapped["University"] = relationship(
        back_populates="language_requirements"
    )

    __table_args__ = (
        Index("idx_lang_req_university_id", "university_id"),
        Index("idx_lang_req_exam_type", "exam_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<LanguageRequirement(id={self.id}, university_id={self.university_id}, "
            f"exam_type='{self.exam_type}', min_score={self.min_score})>"
        )


class University(Base):
    """
    파견 대학 정보 테이블.
    """

    __tablename__ = "university"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="대학교 고유 식별자"
    )
    semester: Mapped[str] = mapped_column(String(100), nullable=False, comment="모집 학기")
    region: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="학교가 위치한 지역 (예: Europe, Asia)"
    )
    nation: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="학교가 속한 국가"
    )
    name_kor: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="대학교 한글 명칭"
    )
    name_eng: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="대학교 영문 명칭"
    )
    min_gpa: Mapped[float] = mapped_column(Float, nullable=False, comment="지원을 위한 최소 GPA")
    significant_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="주요사항"
    )
    remark: Mapped[str] = mapped_column(Text, nullable=False, comment="기타 참고사항 (비고)")
    available_majors: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="교환학생 수강 가능한 전공 목록"
    )
    website_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="공식 홈페이지 주소"
    )

    is_exchange: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="교환학생 파견 가능 여부"
    )
    is_visit: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="방문학생 파견 가능 여부"
    )
    has_review: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="교환학생 수기 존재 여부"
    )
    review_year: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="수기 연도 (예: 2018, 2013-2019)"
    )

    # Relationships
    language_requirements: Mapped[List["LanguageRequirement"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_university_nation", "nation"),
        Index("idx_university_region", "region"),
        Index("idx_university_name_kor", "name_kor"),
    )

    def __repr__(self) -> str:
        return (
            f"<University(id={self.id}, name_kor='{self.name_kor}', nation='{self.nation}')>"
        )


