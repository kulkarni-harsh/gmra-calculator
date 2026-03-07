from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_PREFIX: str
    DEBUG: bool
    DATABASE_URL: str
    OPENCAGE_API_KEY: str
    CENSUS_API_KEY: str
    MAPBOX_API_KEY: str
    ALPHASOPHIA_API_KEY: str

    # Settings for file paths, use cwd as base
    LOOKUP_DIR: Path = Path("resources/lookups")
    TEMPLATES_DIR: Path = Path("resources/templates")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
