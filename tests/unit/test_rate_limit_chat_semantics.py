from __future__ import annotations

"""Verify skip_session_rate_limit avoids a second rate-limit increment for nested chat calls."""

from unittest.mock import patch

from interview_app.security.rate_limiter import _SESSION_KEY
from interview_app.services.interview_generator import generate_questions
from interview_app.utils.types import LLMResponse


def test_generate_questions_skip_session_rate_limit_skips_timestamp() -> None:
    session: dict = {}
    with patch("interview_app.services.interview_generator.LLMClient") as mock_cls:
        mock_cls.return_value.generate_response.return_value = LLMResponse(
            text="1. Tell me about yourself.",
            model="gpt-4o-mini",
            usage=None,
            raw_response_id=None,
        )
        result = generate_questions(
            role_category="Other",
            role_title="Engineer",
            seniority="Mid-Level",
            interview_round="Technical Interview",
            interview_focus="Behavioral / Soft Skills",
            job_description="",
            n_questions=1,
            prompt_strategy="zero_shot",
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=800,
            top_p=1.0,
            session_state=session,
            skip_session_rate_limit=True,
        )

    assert result.ok is True
    assert _SESSION_KEY not in session


def test_generate_questions_without_skip_adds_one_timestamp() -> None:
    session: dict = {}
    with patch("interview_app.services.interview_generator.LLMClient") as mock_cls:
        mock_cls.return_value.generate_response.return_value = LLMResponse(
            text="1. Tell me about yourself.",
            model="gpt-4o-mini",
            usage=None,
            raw_response_id=None,
        )
        result = generate_questions(
            role_category="Other",
            role_title="Engineer",
            seniority="Mid-Level",
            interview_round="Technical Interview",
            interview_focus="Behavioral / Soft Skills",
            job_description="",
            n_questions=1,
            prompt_strategy="zero_shot",
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=800,
            top_p=1.0,
            session_state=session,
            skip_session_rate_limit=False,
        )

    assert result.ok is True
    assert _SESSION_KEY in session
    assert len(session[_SESSION_KEY]) == 1
