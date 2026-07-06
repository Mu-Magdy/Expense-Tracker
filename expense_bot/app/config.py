"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the expense tracker bot."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )

    telegram_token: str = Field(..., alias="TELEGRAM_TOKEN")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        "sqlite+aiosqlite:///./expense.db",
        alias="DATABASE_URL",
    )
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    model_name: str = Field("gpt-4o-mini", alias="MODEL_NAME")
    whisper_model: str = Field("whisper-1", alias="WHISPER_MODEL")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
