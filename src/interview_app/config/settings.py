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


class SecuritySettings(BaseSettings):
    """Configurable thresholds and toggles for the security / guardrail layer."""

    model_config = SettingsConfigDict(env_prefix="SECURITY_", extra="ignore")

    max_input_length: int = Field(
        default=8000,
        description="Maximum allowed characters for a single user input.",
    )
    rate_limit_max_requests: int = Field(
        default=20,
        description="Max LLM requests allowed per rate-limit window.",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate-limit sliding window in seconds.",
    )
    moderation_enabled: bool = Field(
        default=True,
        description="Enable lightweight content moderation.",
    )
    output_max_length: int = Field(
        default=16000,
        description="Maximum characters for model output before truncation.",
    )
    prompt_injection_strict: bool = Field(
        default=False,
        description="When True, use stricter (more false-positives) injection detection.",
    )
    cv_max_file_bytes: int = Field(
        default=5 * 1024 * 1024,
        description="Maximum upload size for CV files (PDF/DOCX).",
    )
    cv_max_text_chars: int = Field(
        default=20_000,
        description="Maximum characters of extracted CV text sent through guardrails and to the LLM.",
    )


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
    sessions_dir: str = Field(
        default="data/sessions",
        description="Directory for lightweight session JSON files (relative to cwd or absolute).",
    )

    security: SecuritySettings = Field(default_factory=SecuritySettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load and cache settings (singleton-style).

    Streamlit re-runs the script frequently; caching avoids repeated env parsing and
    keeps config access fast and consistent during a session.
    """
    return Settings()


def get_security_settings() -> SecuritySettings:
    """Shortcut to access the security sub-config."""
    return get_settings().security

