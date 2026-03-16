from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_PREFIX: str
    DEBUG: bool
    CENSUS_API_KEY: str
    MAPBOX_API_KEY: str
    ALPHASOPHIA_API_KEY: str
    ALLOWED_ORIGINS: str = ""  # comma-separated extra origins; empty = no extras
    AWS_DEFAULT_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_ENDPOINT_URL: str = ""

    # Async job infrastructure
    DYNAMODB_TABLE_NAME: str = "merc-jobs"
    SQS_QUEUE_URL: str = ""

    # Email (Resend)
    RESEND_API_KEY: str = ""
    FRONTEND_URL: str = ""  # e.g. https://yourdomain.com — used to build status links in emails

    # S3 report storage
    S3_BUCKET_NAME: str = "merc-reports"
    S3_REPORTS_PREFIX: str = "reports"
    S3_PRESIGN_EXPIRY_SECONDS: int = 604800  # 7 days

    # Settings for file paths, use cwd as base
    LOOKUP_DIR: Path = Path("resources/lookups")
    TEMPLATES_DIR: Path = Path("resources/templates")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
