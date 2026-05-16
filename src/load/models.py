"""SQLAlchemy models for university exchange program data."""

import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# SQLite only auto-increments for INTEGER PRIMARY KEY, so use an Integer
# variant there while keeping BigInteger elsewhere.
SQLITE_COMPATIBLE_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    """Base class for all models."""


class LanguageRequirement(Base):
    """Parsed language requirement rows for one university offering."""

    __tablename__ = "language_requirement"

    id: Mapped[int] = mapped_column(
        SQLITE_COMPATIBLE_BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="Language requirement primary key",
    )
    university_id: Mapped[int] = mapped_column(
        ForeignKey("university.id", ondelete="CASCADE"),
        nullable=False,
        comment="University row ID",
    )
    language_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Language group such as ENGLISH or JAPANESE",
    )
    exam_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Exam type such as TOEFL, IELTS, or JLPT",
    )
    min_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Minimum score",
    )
    level_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Optional grade or level code",
    )

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
    """One university offering for one semester."""

    __tablename__ = "university"

    id: Mapped[int] = mapped_column(
        SQLITE_COMPATIBLE_BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="University primary key",
    )
    semester: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Single semester for this offering",
    )
    region: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Region",
    )
    nation: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Country",
    )
    name_kor: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Korean university name",
    )
    name_eng: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="English university name",
    )
    min_gpa: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Minimum GPA",
    )
    significant_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Important notes",
    )
    remark: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Merged remark field",
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="University location",
    )
    student_count: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Student count",
    )
    available_majors: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw available majors text",
    )
    available_major: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Parsed available major",
    )
    available_subject: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Parsed subject catalog URL",
    )
    website_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Official website URL",
    )
    badge: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Institution or badge label",
    )
    is_exchange: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether exchange program is available",
    )
    is_visit: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether visiting program is available",
    )
    has_review: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether a student review exists",
    )
    review_year: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Review year or year range",
    )
    language_score: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw language requirement text",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Created at",
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Updated at",
    )

    language_requirements: Mapped[List["LanguageRequirement"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("name_eng", "nation", "semester", name="uq_university_semester"),
        Index("idx_university_nation", "nation"),
        Index("idx_university_region", "region"),
        Index("idx_university_name_kor", "name_kor"),
        Index(
            "idx_university_name_eng_nation_semester",
            "name_eng",
            "nation",
            "semester",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<University(id={self.id}, name_kor='{self.name_kor}', "
            f"nation='{self.nation}', semester='{self.semester}')>"
        )
