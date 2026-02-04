"""Configuration settings for the ETL pipeline."""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+psycopg2://user:password@host:5432/dbname"

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "beyondu-raw-data"
    aws_region: str = "ap-northeast-2"

    # Paths
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")

    # ETL Settings
    excluded_institutions: List[str] = ["SAF", "ACUCA"]

    # Environment
    env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
