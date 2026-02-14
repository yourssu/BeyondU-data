"""Database operations for loading processed data."""

from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.transform.parser import (
    GPAParser,
    LanguageParser,
    ParsedLanguageRequirement,
    ReviewParser,
    WebsiteURLParser,
)

from .models import Base, LanguageRequirement, University


class DatabaseLoader:
    """Load processed data into the database."""

    COUNTRY_TO_REGION_MAP = {
        "미국": "북미",
        "캐나다": "북미",
        "멕시코": "북미",
        "독일": "유럽",
        "영국": "유럽",
        "터키": "유럽",
        "프랑스": "유럽",
        "스페인": "유럽",
        "이탈리아": "유럽",
        "네덜란드": "유럽",
        "스위스": "유럽",
        "오스트리아": "유럽",
        "체코": "유럽",
        "폴란드": "유럽",
        "헝가리": "유럽",
        "스웨덴": "유럽",
        "노르웨이": "유럽",
        "덴마크": "유럽",
        "핀란드": "유럽",
        "벨기에": "유럽",
        "일본": "아시아",
        "중국": "아시아",
        "대만": "아시아",
        "키르기즈스탄": "아시아",
        "싱가포르": "아시아",
        "말레이시아": "아시아",
        "인도네시아": "아시아",
        "베트남": "아시아",
        "태국": "아시아",
        "호주": "오세아니아",
        "브라질": "남미",
        "칠레": "남미",
    }

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        print(f"DEBUG: DATABASE_URL = {self.database_url}, type = {type(self.database_url)}")
        if not self.database_url or "://" not in self.database_url:
            raise ValueError(f"Invalid DATABASE_URL: {self.database_url}")
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._language_parser = LanguageParser()
        self._gpa_parser = GPAParser()
        self._website_url_parser = WebsiteURLParser()
        self._review_parser = ReviewParser()

    def get_region_from_nation(self, nation: str) -> Optional[str]:
        """Get region from nation using the mapping."""
        return self.COUNTRY_TO_REGION_MAP.get(nation)

    def create_tables(self) -> None:
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all tables."""
        Base.metadata.drop_all(self.engine)

    def _load_language_requirements(
        self,
        session: Session,
        university_id: int,
        parsed_req: ParsedLanguageRequirement,
        excluded_exams_from_note: List[str],
    ) -> int:
        """Load parsed language requirements into the database."""
        session.execute(
            delete(LanguageRequirement).where(LanguageRequirement.university_id == university_id)
        )
        for score_info in parsed_req.scores:
            record = LanguageRequirement(
                university_id=university_id,
                exam_type=score_info.exam_type,
                min_score=score_info.min_score,
                level_code=score_info.level_code,
                language_group=score_info.language_group,
                is_available=not (
                    score_info.exam_type in parsed_req.excluded_tests
                    or score_info.exam_type in excluded_exams_from_note
                ),
            )
            session.add(record)
        return len(parsed_req.scores)

    def load_universities_dataframe(self, df: pd.DataFrame) -> Dict[str, int]:
        """Load a cleaned DataFrame into the database using an upsert strategy."""
        stats = {"inserted": 0, "updated": 0, "skipped": 0, "language_reqs": 0}
        with self.SessionLocal() as session:
            # Use name_eng and nation as a composite key to find existing records
            eng_names = df.get("name_eng", pd.Series()).dropna().unique()
            existing_map = {}
            if len(eng_names) > 0:
                stmt = select(University).where(University.name_eng.in_(eng_names))
                for uni in session.execute(stmt).scalars():
                    existing_map[(uni.name_eng, uni.nation)] = uni

            for _, row in df.iterrows():
                name_kor = self._get_field(row, "name_kor")
                name_eng = self._get_field(row, "name_eng")
                nation = self._get_field(row, "nation")

                if not all([name_kor, name_eng, nation]):
                    stats["skipped"] += 1
                    continue

                program_type_str = self._get_field(row, "program_type", "일반교환")
                new_semester_from_file = self._get_field(row, "semester")

                # Get text for parsing language scores
                lang_req_parse_text = self._get_field(row, "language_requirement")

                # Get region and map if unclassified
                region = self._get_field(row, "region", "미분류")
                if region == "미분류":
                    mapped_region = self.get_region_from_nation(nation)
                    if mapped_region:
                        region = mapped_region

                has_review, review_year = self._review_parser.parse(self._get_field(row, "review_raw"))

                # Parse exclusions from significant_note
                sig_note = self._get_field(row, "significant_note")
                excluded_exams = self._language_parser.parse_exclusions(sig_note)

                data = {
                    "semester": new_semester_from_file,
                    "region": region,
                                    "nation": nation,
                                    "name_kor": name_kor,
                                    "name_eng": name_eng,
                                    "badge": self._get_field(row, "institution"),
                                    "min_gpa": self._gpa_parser.parse(self._get_field(row, "min_gpa")) or 0.0,
                                    "significant_note": self._get_field(row, "significant_note"),
                                    "remark": "\n".join(filter(None, [self._get_field(row, "remark"), self._get_field(row, "remark_ref")])),
                                    "available_majors": self._get_field(row, "available_majors"),
                                    "website_url": self._website_url_parser.parse(
                                        self._get_field(row, "website_url")                    ),
                    "is_exchange": "교환" in program_type_str,
                    "is_visit": "방문" in program_type_str,
                    "available_semester": self._get_field(row, "available_semester"), # 이 부분은 더 이상 모델에 없음

                }

                # 모델에서 제거된 컬럼이 data에 남아있을 경우 제거
                if "available_semester" in data:
                    del data["available_semester"]
                if "thumbnail_url" in data: # 혹시 모를 경우를 대비하여 추가
                    del data["thumbnail_url"]

                composite_key = (name_eng, nation)
                university = existing_map.get(composite_key)

                if university:  # Update existing university
                    # Handle cumulative update for semester
                    if new_semester_from_file:
                        existing_semesters = (
                            set(university.semester.split(", "))
                            if university.semester
                            else set()
                        )
                        existing_semesters.add(new_semester_from_file)
                        data["semester"] = ", ".join(
                            sorted(list(existing_semesters), reverse=True)
                        )

                    for key, value in data.items():
                        if value is not None:
                            setattr(university, key, value)
                    stats["updated"] += 1
                else:  # Insert new university
                    university = University(**data)
                    session.add(university)
                    stats["inserted"] += 1
                    # Add to map to allow updates within the same dataframe run
                    existing_map[composite_key] = university

                if university and lang_req_parse_text:
                    # We need the ID for language requirements, so flush to get it
                    if not university.id:
                        session.flush()

                    parsed_req = self._language_parser.parse(
                        lang_req_parse_text, region=university.region
                    )
                    if not parsed_req.is_optional and university.id:
                        count = self._load_language_requirements(
                            session, university.id, parsed_req, excluded_exams
                        )
                        stats["language_reqs"] += count

            session.commit()

        return stats

    def _get_field(self, row: pd.Series, field_name: str, default: Any = None) -> Any:
        value = row.get(field_name)
        try:
            import pandas as pd
            if value is None or pd.isna(value) or (isinstance(value, str) and not value.strip()):
                return default
        except ImportError:
            if value is None or (isinstance(value, str) and not value.strip()):
                return default
        return str(value).strip() if isinstance(value, str) else value

    def get_all_universities(self) -> List[University]:
        with self.SessionLocal() as session:
            return list(session.execute(select(University).order_by(University.name_kor)).scalars().all())

    def get_language_requirements(self, university_id: int) -> List[LanguageRequirement]:
        with self.SessionLocal() as session:
            stmt = select(LanguageRequirement).where(LanguageRequirement.university_id == university_id)
            return list(session.execute(stmt).scalars().all())

    def get_all_language_requirements(self) -> List[LanguageRequirement]:
        with self.SessionLocal() as session:
            return list(session.execute(select(LanguageRequirement).order_by(LanguageRequirement.university_id, LanguageRequirement.exam_type)).scalars().all())

    def search_universities_by_language(self, exam_type: str, user_score: float) -> List[University]:
        with self.SessionLocal() as session:
            stmt = (
                select(University)
                .join(LanguageRequirement)
                .where(
                    LanguageRequirement.exam_type == exam_type,
                    LanguageRequirement.min_score <= user_score,
                )
                .distinct()
            )
            return list(session.execute(stmt).scalars().all())
