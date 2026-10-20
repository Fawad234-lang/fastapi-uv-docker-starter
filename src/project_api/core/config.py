"""Typed, cached application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Environment-backed settings validated by Pydantic once and cached."""

    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_version: str = "0.1.0"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    llm_timeout_seconds: float = Field(default=30, gt=0, le=300)
    llm_max_input_length: int = Field(default=2000, ge=1, le=2000)
    llm_max_output_tokens: int = Field(default=512, ge=1, le=8192)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one settings instance instead of re-reading the environment."""
    return Settings()
