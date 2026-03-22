from __future__ import annotations

"""Unit tests for security configuration."""

import pytest

from interview_app.config.settings import SecuritySettings, Settings, get_security_settings


def test_security_defaults() -> None:
    sec = SecuritySettings()
    assert sec.max_input_length == 8000
    assert sec.rate_limit_max_requests == 20
    assert sec.rate_limit_window_seconds == 60
    assert sec.moderation_enabled is True
    assert sec.output_max_length == 16000
    assert sec.prompt_injection_strict is False


def test_security_settings_override() -> None:
    sec = SecuritySettings(
        max_input_length=4000,
        rate_limit_max_requests=5,
        moderation_enabled=False,
    )
    assert sec.max_input_length == 4000
    assert sec.rate_limit_max_requests == 5
    assert sec.moderation_enabled is False


def test_settings_includes_security() -> None:
    """The main Settings model should carry a SecuritySettings sub-model."""
    s = Settings(openai_api_key="sk-test1234567890abcdef")
    assert hasattr(s, "security")
    assert isinstance(s.security, SecuritySettings)


def test_get_security_settings_returns_instance() -> None:
    sec = get_security_settings()
    assert isinstance(sec, SecuritySettings)


def test_security_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """SecuritySettings should respect SECURITY_ prefixed env vars."""
    monkeypatch.setenv("SECURITY_RATE_LIMIT_MAX_REQUESTS", "99")
    monkeypatch.setenv("SECURITY_MODERATION_ENABLED", "false")
    sec = SecuritySettings()
    assert sec.rate_limit_max_requests == 99
    assert sec.moderation_enabled is False
