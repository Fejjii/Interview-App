from __future__ import annotations

"""
Centralized configuration (settings) for the app.

This project uses environment variables as the primary configuration mechanism.
For local development, a `.env` file in the project root is supported.

Typical flow:
- `streamlit_app.py` loads `.env` so env vars are available
- `LLMClient` calls `get_settings()` to read OPENAI_API_KEY, defaults, etc.
"""

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
    """
    Load and cache settings (singleton-style).

    Streamlit re-runs the script frequently; caching avoids repeated env parsing and
    keeps config access fast and consistent during a session.
    """
    return Settings()

