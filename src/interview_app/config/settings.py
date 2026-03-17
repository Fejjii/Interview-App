from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and an optional `.env` file.

    Notes:
    - `.env` is optional; environment variables always take precedence.
    - Keep secrets out of source control; use `.env.example` as documentation.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="dev", description="Application environment (dev/prod/test).")

    openai_api_key: SecretStr | None = Field(
        default=None,
        description="OpenAI API key. Prefer setting via environment variable OPENAI_API_KEY.",
    )
    openai_model: str = Field(default="gpt-4o-mini", description="Default OpenAI model name.")
    openai_temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Default sampling temperature."
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

