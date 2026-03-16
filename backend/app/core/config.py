from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_PREFIX: str
    DEBUG: bool
    OPENCAGE_API_KEY: str
    CENSUS_API_KEY: str
    MAPBOX_API_KEY: str
    ALPHASOPHIA_API_KEY: str
    ALLOWED_ORIGINS: str = ""  # comma-separated extra origins; empty = no extras

    # Async job infrastructure
    DYNAMODB_TABLE_NAME: str = "merc-jobs"
    SQS_QUEUE_URL: str = ""

    # Email (Mailgun)
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""  # e.g. yourdomain.com — set by ECS env var

    # Settings for file paths, use cwd as base
    LOOKUP_DIR: Path = Path("resources/lookups")
    TEMPLATES_DIR: Path = Path("resources/templates")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
