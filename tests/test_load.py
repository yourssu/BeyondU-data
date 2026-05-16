"""Tests for database loading behavior."""

import pandas as pd
import pytest

from src.load.database import DatabaseLoader


@pytest.fixture
def sqlite_loader(tmp_path):
    """Create a loader backed by a temporary SQLite database."""
    db_path = tmp_path / "test_loader.db"
    loader = DatabaseLoader(f"sqlite:///{db_path.as_posix()}")
    loader.create_tables()
    return loader


def test_same_university_is_split_by_semester(sqlite_loader: DatabaseLoader) -> None:
    """The same university should create one row per semester."""
    df = pd.DataFrame(
        [
            {
                "name_kor": "Semester University KR",
                "name_eng": "Semester University",
                "nation": "Semester Land",
                "region": "Test Region",
                "program_type": "교환학생",
                "semester": "2024-1",
                "institution": "Semester Badge",
                "min_gpa": "3.5",
                "significant_note": "",
                "language_requirement": "TOEFL 90",
                "website_url": "http://semester.edu",
                "available_majors": "Computer Science",
                "review_raw": "X",
            },
            {
                "name_kor": "Semester University KR",
                "name_eng": "Semester University",
                "nation": "Semester Land",
                "region": "Test Region",
                "program_type": "교환학생",
                "semester": "2024-2",
                "institution": "Semester Badge",
                "min_gpa": "3.7",
                "significant_note": "",
                "language_requirement": "TOEFL 95",
                "website_url": "http://semester.edu",
                "available_majors": "Computer Science",
                "review_raw": "Y(2024)",
            },
        ]
    )

    stats = sqlite_loader.load_universities_dataframe(df)

    assert stats["inserted"] == 2
    assert stats["updated"] == 0

    universities = sqlite_loader.get_all_universities()
    assert len(universities) == 2
    assert sorted(uni.semester for uni in universities) == ["2024-1", "2024-2"]
    assert all("," not in uni.semester for uni in universities)


def test_same_semester_updates_existing_row(sqlite_loader: DatabaseLoader) -> None:
    """The same university and semester should still upsert into one row."""
    initial_df = pd.DataFrame(
        [
            {
                "name_kor": "Update University KR",
                "name_eng": "Update University",
                "nation": "Update Land",
                "region": "Test Region",
                "program_type": "교환학생",
                "semester": "2024-1",
                "institution": "Initial Badge",
                "min_gpa": "3.0",
                "significant_note": "",
                "language_requirement": "TOEFL 80",
                "website_url": "http://update.edu",
                "available_majors": "Economics",
                "review_raw": "X",
            }
        ]
    )
    update_df = pd.DataFrame(
        [
            {
                "name_kor": "Update University KR",
                "name_eng": "Update University",
                "nation": "Update Land",
                "region": "Test Region",
                "program_type": "교환학생",
                "semester": "2024-1",
                "institution": "Updated Badge",
                "min_gpa": "3.8",
                "significant_note": "",
                "language_requirement": "TOEFL 95",
                "website_url": "http://update.edu/new",
                "available_majors": "Economics",
                "review_raw": "Y(2025)",
            }
        ]
    )

    sqlite_loader.load_universities_dataframe(initial_df)
    stats = sqlite_loader.load_universities_dataframe(update_df)

    assert stats["inserted"] == 0
    assert stats["updated"] == 1

    universities = sqlite_loader.get_all_universities()
    assert len(universities) == 1

    university = universities[0]
    assert university.semester == "2024-1"
    assert university.badge == "Updated Badge"
    assert university.min_gpa == 3.8
    assert university.review_year == "2025"


def test_unknown_region_is_backfilled_from_nation(sqlite_loader: DatabaseLoader) -> None:
    """Unknown region values should be mapped from nation before save."""
    df = pd.DataFrame(
        [
            {
                "name_kor": "터키 대학",
                "name_eng": "Turkey University",
                "nation": "터키",
                "region": "Unknown",
                "program_type": "교환학생",
                "semester": "2023-1",
                "institution": "Badge",
                "min_gpa": "3.0",
                "significant_note": "",
                "language_requirement": "",
                "website_url": "http://turkey.edu",
                "available_majors": "Business",
                "review_raw": "X",
            }
        ]
    )

    stats = sqlite_loader.load_universities_dataframe(df)

    assert stats["inserted"] == 1
    universities = sqlite_loader.get_all_universities()
    assert len(universities) == 1
    assert universities[0].region == "유럽"


def test_unknown_region_is_backfilled_for_kyrgyzstan(sqlite_loader: DatabaseLoader) -> None:
    """Unknown region for Kyrgyzstan should be saved as Asia."""
    df = pd.DataFrame(
        [
            {
                "name_kor": "키르기즈 대학",
                "name_eng": "Kyrgyz University",
                "nation": "키르기즈스탄",
                "region": "Unknown",
                "program_type": "교환학생",
                "semester": "2023-2",
                "institution": "Badge",
                "min_gpa": "3.0",
                "significant_note": "",
                "language_requirement": "",
                "website_url": "http://kyrgyz.edu",
                "available_majors": "Business",
                "review_raw": "X",
            }
        ]
    )

    stats = sqlite_loader.load_universities_dataframe(df)

    assert stats["inserted"] == 1
    universities = sqlite_loader.get_all_universities()
    assert len(universities) == 1
    assert universities[0].region == "아시아"
