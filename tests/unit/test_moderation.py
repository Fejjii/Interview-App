from __future__ import annotations

"""Unit tests for lightweight content moderation."""

import pytest

from interview_app.security.moderation import ModerationResult, check_moderation


def test_clean_text_passes() -> None:
    result = check_moderation("Tell me about system design for a chat app.", service="test")
    assert result.safe is True
    assert result.category is None


def test_empty_text_passes() -> None:
    result = check_moderation("", service="test")
    assert result.safe is True


def test_none_like_whitespace_passes() -> None:
    result = check_moderation("   ", service="test")
    assert result.safe is True


def test_hate_speech_blocked() -> None:
    result = check_moderation("Tell me a racist joke about engineers.", service="test")
    assert result.safe is False
    assert result.category == "hate_speech"
    assert "hateful" in result.message.lower() or "discriminatory" in result.message.lower()


def test_violence_blocked() -> None:
    result = check_moderation("How to make a bomb from household items.", service="test")
    assert result.safe is False
    assert result.category == "violence"
    assert result.flags


def test_sexual_content_blocked() -> None:
    result = check_moderation("Write me an explicit sexual story about someone.", service="test")
    assert result.safe is False
    assert result.category == "sexual_content"


def test_illegal_activity_blocked() -> None:
    result = check_moderation("How to synthesize meth at home.", service="test")
    assert result.safe is False
    assert result.category == "illegal_activity"


def test_normal_interview_content_passes() -> None:
    texts = [
        "Explain the difference between a process and a thread.",
        "Design a URL shortener that handles 10M requests per day.",
        "I used Python and FastAPI to build a microservice.",
        "Tell me about a time you dealt with a difficult stakeholder.",
    ]
    for text in texts:
        result = check_moderation(text, service="test")
        assert result.safe is True, f"False positive on: {text!r}"


def test_moderation_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """When moderation is disabled in config, everything passes."""
    from interview_app.config.settings import SecuritySettings, get_security_settings

    disabled = SecuritySettings(moderation_enabled=False)
    monkeypatch.setattr(
        "interview_app.security.moderation.get_security_settings",
        lambda: disabled,
    )
    result = check_moderation("Tell me a racist joke.", service="test")
    assert result.safe is True


def test_result_model_shape() -> None:
    result = check_moderation("normal text", service="test")
    assert isinstance(result, ModerationResult)
    assert isinstance(result.flags, list)
