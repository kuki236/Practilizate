from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PRACTILIZATE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://practilizate:practilizate@localhost:5433/practilizate",
        validation_alias=AliasChoices("DATABASE_URL", "PRACTILIZATE_DATABASE_URL"),
    )
    source: Literal["fixtures", "live"] = "fixtures"
    as_of: date = date(2026, 10, 29)
    rate_limit_seconds: float = 1.0
    user_agent: str = "Practilizate/0.1 (educational project)"
    output_dir: Path = Path("data/processed")
    artifacts_dir: Path = Path("artifacts")
    fixtures_dir: Path = Path("data/fixtures")
    cache_dir: Path = Path("data/raw/cache")
    log_level: str = "INFO"
    max_pages_per_career: int = 50
    request_timeout_seconds: float = 30.0
    salary_min: float = 0.0
    salary_max: float = 12000.0


def load_settings(**overrides: object) -> Settings:
    return Settings(**overrides)
