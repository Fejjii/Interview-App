"""Mapping helpers for prompt strategy labels ↔ internal keys."""

from interview_app.app.ui_settings import (
    COMPARE_PROMPT_STRATEGY_KEYS,
    label_for_prompt_strategy,
    prompt_strategy_key_from_label,
)


def test_prompt_strategy_key_from_label_round_trip() -> None:
    assert prompt_strategy_key_from_label("Zero-shot") == "zero_shot"
    assert prompt_strategy_key_from_label("Chain-of-thought") == "chain_of_thought"
    assert label_for_prompt_strategy("few_shot") == "Few-shot"
    assert label_for_prompt_strategy("structured_output") == "Structured Output"


def test_unknown_label_falls_back() -> None:
    assert prompt_strategy_key_from_label("Not a real label") == "zero_shot"


def test_compare_keys_subset() -> None:
    assert COMPARE_PROMPT_STRATEGY_KEYS == ("zero_shot", "few_shot", "chain_of_thought")
