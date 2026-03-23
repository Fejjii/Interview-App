"""UI configuration snapshot (``UISettings``) and workspace tab labels.

Produced by ``app/controls.render_sidebar_configuration`` and passed into
``layout`` and services so LLM parameters stay consistent across tabs.

Immutable: ``UISettings`` is a frozen dataclass suitable for threading through
pure functions without accidental mutation.
"""

from __future__ import annotations

from dataclasses import dataclass

WORKSPACE_TAB_LABELS: tuple[str, ...] = (
    "Mock Interview",
    "Interview Questions",
    "CV Interview Prep",
    "Feedback / Evaluation",
)


@dataclass(frozen=True)
class UISettings:
    """All UI-controlled settings that affect prompt building and LLM calls."""

    role_category: str
    role_title: str
    seniority: str
    interview_round: str
    interview_focus: str
    job_description: str
    persona: str
    question_difficulty_mode: str
    effective_question_difficulty: str
    prompt_strategy: str
    model_preset: str
    temperature: float
    top_p: float
    max_tokens: int
    show_debug: bool
    response_language: str
