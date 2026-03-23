"""Usage mode validation, masking, and LLM key resolution."""

from __future__ import annotations

import pytest

from interview_app.app.usage_mode import (
    KEY_BYO_OPENAI_API_KEY,
    KEY_USAGE_MODE,
    UsageMode,
    key_tail_from_masked_hint,
    mask_api_key_for_display,
    openai_api_key_for_llm,
    validate_openai_api_key_format,
)


def test_validate_accepts_typical_openai_key_shape() -> None:
    ok, err = validate_openai_api_key_format("sk-12345678901234567890123456789012")
    assert ok is True
    assert err == ""


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "pk-live-wrong",
        "sk-short",
        "sk spaces not allowed here " + "x" * 20,
    ],
)
def test_validate_rejects_malformed_keys(bad: str) -> None:
    ok, err = validate_openai_api_key_format(bad)
    assert ok is False
    assert err


def test_mask_never_shows_full_key() -> None:
    k = "sk-12345678901234567890123456789012"
    m = mask_api_key_for_display(k)
    assert "12345678901234567890123456789012" not in m
    assert m.endswith("9012")
    assert m.startswith("sk-...")


def test_key_tail_from_masked_hint() -> None:
    assert key_tail_from_masked_hint("sk-...A1b2") == "A1b2"
    assert key_tail_from_masked_hint("") is None


def test_openai_api_key_for_llm_demo_returns_none() -> None:
    ss = {KEY_USAGE_MODE: UsageMode.DEMO.value}
    assert openai_api_key_for_llm(ss) is None


def test_openai_api_key_for_llm_byo_returns_secret() -> None:
    ss = {
        KEY_USAGE_MODE: UsageMode.BYO.value,
        KEY_BYO_OPENAI_API_KEY: "sk-12345678901234567890123456789012",
    }
    assert openai_api_key_for_llm(ss) == "sk-12345678901234567890123456789012"


def test_openai_api_key_for_llm_byo_missing_secret() -> None:
    ss = {KEY_USAGE_MODE: UsageMode.BYO.value}
    assert openai_api_key_for_llm(ss) is None
