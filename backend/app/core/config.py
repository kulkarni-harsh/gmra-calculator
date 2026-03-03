from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_V1_PREFIX: str
    DEBUG: bool
    DATABASE_URL: str
    OPENCAGE_API_KEY: SecretStr

    # Settings for file paths
    LOOKUP_DIR: Path = Path("resources/lookups")
    TEMPLATES_DIR: Path = Path("resources/templates")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
