"""Mock interview JSON export: structure and filename safety."""

from __future__ import annotations

import json

from interview_app.app.ui_settings import UISettings
from interview_app.utils.mock_interview_export import (
    build_mock_interview_export_payload,
    mock_interview_export_filename,
    sanitize_export_filename_part,
)
from interview_app.utils.types import ChatMessage


def test_sanitize_export_filename_part() -> None:
    assert sanitize_export_filename_part("") == "session"
    assert ".." not in sanitize_export_filename_part("../etc/passwd")
    assert sanitize_export_filename_part("My Session!") == "My_Session"


def test_build_mock_interview_export_payload_empty_messages() -> None:
    settings = UISettings(
        role_category="Engineering",
        role_title="Backend Dev",
        seniority="Mid",
        interview_round="Technical",
        interview_focus="Algorithms",
        job_description="JD text",
        persona="Professional",
        question_difficulty_mode="Auto",
        effective_question_difficulty="medium",
        prompt_strategy="zero_shot",
        model_preset="gpt-4o-mini",
        temperature=0.7,
        top_p=0.95,
        max_tokens=800,
        show_debug=False,
        response_language="en",
        usage_mode="demo",
        byo_key_hint=None,
    )
    payload = build_mock_interview_export_payload(
        settings=settings,
        messages=[],
        session_title="",
    )
    assert payload["mode"] == "mock_interview"
    assert payload["messages"] == []
    assert payload["generation_config"]["temperature"] == 0.7
    assert payload["role_context"]["job_description"] == "JD text"
    text = json.dumps(payload, ensure_ascii=False)
    assert "mock_interview" in text


def test_build_mock_interview_export_payload_with_timestamps() -> None:
    settings = UISettings(
        role_category="Engineering",
        role_title="Backend Dev",
        seniority="Mid",
        interview_round="Technical",
        interview_focus="Algorithms",
        job_description="",
        persona="Professional",
        question_difficulty_mode="Auto",
        effective_question_difficulty="medium",
        prompt_strategy="few_shot",
        model_preset="gpt-4o-mini",
        temperature=0.5,
        top_p=1.0,
        max_tokens=500,
        show_debug=False,
        response_language="en",
        usage_mode="demo",
        byo_key_hint=None,
    )
    msgs = [
        ChatMessage(role="user", content="Hi", timestamp="2025-01-01T12:00:00.000Z"),
        ChatMessage(role="assistant", content="Hello"),
    ]
    payload = build_mock_interview_export_payload(
        settings=settings,
        messages=msgs,
        session_title="Practice",
    )
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["timestamp"] == "2025-01-01T12:00:00.000Z"
    assert "timestamp" not in payload["messages"][1]


def test_mock_interview_export_filename_format() -> None:
    name = mock_interview_export_filename("Test Session")
    assert name.startswith("mock_interview_Test_Session_")
    assert name.endswith(".json")
