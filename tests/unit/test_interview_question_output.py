"""Tests for JSON question output parsing."""

from __future__ import annotations

from interview_app.utils.interview_question_output import (
    first_question_text_from_output,
    parse_generation_questions_list,
    try_parse_questions_json,
)


def test_try_parse_questions_json_valid() -> None:
    raw = """
    {"questions": [{"question": "Q1?", "skill_tested": "x", "difficulty": "Hard", "why_it_matters": "y"}]}
    """
    out = try_parse_questions_json(raw)
    assert out is not None
    assert len(out) == 1
    assert out[0]["question"] == "Q1?"


def test_try_parse_questions_json_with_fences() -> None:
    raw = """```json
{"questions": [{"question": "Hello?", "skill_tested": "a", "difficulty": "b", "why_it_matters": "c"}]}
```"""
    out = try_parse_questions_json(raw)
    assert out is not None
    assert out[0]["question"] == "Hello?"


def test_first_question_from_json() -> None:
    t = '{"questions": [{"question": "First"}]}'
    assert first_question_text_from_output(t) == "First"


def test_first_question_from_plain_text_returns_none() -> None:
    assert first_question_text_from_output("1. Something") is None


def test_parse_generation_questions_list_numbered() -> None:
    text = """1. First question here?
2) Second question
3. Third"""
    out = parse_generation_questions_list(text, "zero_shot")
    assert len(out) == 3
    assert "First question" in out[0]


def test_parse_generation_questions_list_json() -> None:
    raw = '{"questions": [{"question": "A?", "skill_tested": "x", "difficulty": "Hard", "why_it_matters": "y"}]}'
    out = parse_generation_questions_list(raw, "structured_output")
    assert out == ["A?"]
