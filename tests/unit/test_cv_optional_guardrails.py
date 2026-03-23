from __future__ import annotations

"""Optional CV fields must not run guardrails on empty strings (matches interview_generator JD pattern)."""

import pytest

from interview_app.services import cv_interview_service as svc
from interview_app.utils.types import LLMResponse


def _extraction_json() -> str:
    return (
        '{"profile_summary":"X","skills":["S"],"tools_technologies":[],"work_experience":[],'
        '"projects":[],"education":[],"certifications":[],"detected_roles":[]}'
    )


def _generation_json() -> str:
    return (
        '{"candidate_summary":"C","key_skills":[],"detected_roles":[],"themes_from_cv":[],'
        '"interview_questions":[]}'
    )


def test_empty_optional_company_and_job_do_not_add_failed_guardrails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty target company + extra job context must not populate guards with invalid_input."""
    calls: list[int] = []

    class FakeClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def generate_response(self, **kwargs: object) -> LLMResponse:
            calls.append(1)
            if len(calls) == 1:
                return LLMResponse(text=_extraction_json(), model="m", usage=None)
            return LLMResponse(text=_generation_json(), model="m", usage=None)

    monkeypatch.setattr(svc, "LLMClient", FakeClient)
    monkeypatch.setattr(
        svc,
        "extract_text_from_cv_bytes",
        lambda **kwargs: "Experienced engineer with Python and AWS.",
    )

    result = svc.run_cv_interview_pipeline(
        filename="cv.pdf",
        file_bytes=b"%PDF-1.4\n",
        target_role="Engineer",
        interview_type="mixed",
        difficulty="medium",
        n_questions=2,
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=2000,
        top_p=None,
        session_state={"_security_rate_limit_timestamps": []},
        target_company="",
        extra_job_context="   ",
    )

    assert result.ok
    assert "cv_extra_job_context" not in result.guardrails
    assert "cv_target_company" not in result.guardrails


def test_empty_extract_after_normalize_returns_actionable_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        svc,
        "extract_text_from_cv_bytes",
        lambda **kwargs: "",
    )

    result = svc.run_cv_interview_pipeline(
        filename="cv.pdf",
        file_bytes=b"%PDF-1.4\n",
        target_role="Engineer",
        interview_type="mixed",
        difficulty="medium",
        n_questions=1,
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=500,
        top_p=None,
        session_state={"_security_rate_limit_timestamps": []},
    )

    assert not result.ok
    assert "Could not extract readable text" in (result.error or "")
    assert "scanned" in (result.error or "").lower() or "image" in (result.error or "").lower()


def test_pdf_dependency_error_message_includes_pip_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    from interview_app.cv.exceptions import CVExtractionError

    def boom(**kwargs: object) -> str:
        raise CVExtractionError(
            "PDF text extraction needs the 'pypdf' package. Run: pip install pypdf"
        )

    monkeypatch.setattr(svc, "extract_text_from_cv_bytes", boom)

    result = svc.run_cv_interview_pipeline(
        filename="cv.pdf",
        file_bytes=b"%PDF-1.4\n",
        target_role="Engineer",
        interview_type="mixed",
        difficulty="medium",
        n_questions=1,
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=500,
        top_p=None,
        session_state={"_security_rate_limit_timestamps": []},
    )

    assert not result.ok
    assert "pypdf" in (result.error or "").lower()
