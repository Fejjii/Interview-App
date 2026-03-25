"""Single source of truth for mock-interview configuration on each turn.

Merges live sidebar ``UISettings`` with persisted ``session_meta`` (saved / loaded
sessions) so an empty sidebar role field does not drop a title that still exists
in the active session snapshot.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

from interview_app.app.ui_settings import UISettings
from interview_app.utils.types import SessionMeta


@dataclass(frozen=True)
class EffectiveInterviewConfig:
    """Resolved inputs for mock-interview LLM calls after session/sidebar merge."""

    role_category: str
    role_title: str
    seniority: str
    interview_round: str
    interview_focus: str
    job_description: str
    interviewer_persona: str
    response_language: str
    prompt_strategy: str
    effective_question_difficulty: str
    model_preset: str
    temperature: float
    top_p: float
    max_tokens: int
    show_debug: bool


def _coerce_session_meta(raw: object) -> SessionMeta | None:
    if raw is None:
        return None
    if isinstance(raw, SessionMeta):
        return raw
    if isinstance(raw, Mapping):
        try:
            return SessionMeta.model_validate(dict(raw))
        except Exception:
            return None
    return None


def get_effective_interview_config(
    settings: UISettings,
    session_state: MutableMapping[str, Any] | None,
) -> EffectiveInterviewConfig:
    """
    Build effective config: sidebar wins when non-empty; otherwise fall back to
    ``session_meta`` fields from a loaded saved interview.
    """
    meta = _coerce_session_meta(session_state.get("session_meta") if session_state else None)

    def _pick(sidebar: str, saved: str) -> str:
        s = (sidebar or "").strip()
        if s:
            return s
        return (saved or "").strip()

    role_category = _pick(settings.role_category, meta.role_category if meta else "")
    role_title = _pick(settings.role_title, meta.role_title if meta else "")
    seniority = _pick(settings.seniority, meta.seniority if meta else "")
    interview_round = _pick(settings.interview_round, meta.interview_round if meta else "")
    interview_focus = _pick(settings.interview_focus, meta.interview_focus if meta else "")
    persona = _pick(settings.persona, meta.persona if meta else "")

    top_p = float(settings.top_p) if settings.top_p is not None else 1.0

    return EffectiveInterviewConfig(
        role_category=role_category or (settings.role_category or "").strip(),
        role_title=role_title,
        seniority=seniority or (settings.seniority or "").strip(),
        interview_round=interview_round or (settings.interview_round or "").strip(),
        interview_focus=interview_focus or (settings.interview_focus or "").strip(),
        job_description=(settings.job_description or "").strip(),
        interviewer_persona=persona or (settings.persona or "").strip(),
        response_language=settings.response_language,
        prompt_strategy=settings.prompt_strategy,
        effective_question_difficulty=settings.effective_question_difficulty,
        model_preset=settings.model_preset,
        temperature=float(settings.temperature),
        top_p=top_p,
        max_tokens=int(settings.max_tokens),
        show_debug=settings.show_debug,
    )
