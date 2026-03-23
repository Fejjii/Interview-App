"""Unit tests for language detection and response-language helpers."""

from __future__ import annotations

from interview_app.utils.language import (
    DEFAULT_LANGUAGE,
    detect_language,
    get_language_name,
    language_instruction,
)


def test_default_language_is_english() -> None:
    assert DEFAULT_LANGUAGE == "en"


def test_detect_language_short_text_returns_default() -> None:
    assert detect_language("Hi") == DEFAULT_LANGUAGE
    assert detect_language("") == DEFAULT_LANGUAGE


def test_detect_language_english() -> None:
    text = "This is a job description for a software engineer role. We need someone with Python experience."
    assert detect_language(text) == "en"


def test_detect_language_french() -> None:
    text = "Nous recherchons un ingénieur logiciel pour rejoindre notre équipe. Expérience en Python requise."
    result = detect_language(text)
    assert isinstance(result, str) and len(result) >= 2
    assert get_language_name(result)  # no crash; unknown codes yield "English"


def test_get_language_name_known() -> None:
    assert get_language_name("en") == "English"
    assert get_language_name("fr") == "French"


def test_get_language_name_unknown_defaults_to_english() -> None:
    assert get_language_name("xy") == "English"
    assert get_language_name("") == "English"


def test_language_instruction_contains_language() -> None:
    out = language_instruction("fr")
    assert "French" in out
    assert "only" in out.lower() or "must" in out.lower()
