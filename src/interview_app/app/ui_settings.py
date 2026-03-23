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

# Sidebar labels and internal keys used by `prompt_strategies` / `interview_generator`.
PROMPT_STRATEGY_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Zero-shot", "zero_shot"),
    ("Few-shot", "few_shot"),
    ("Chain-of-thought", "chain_of_thought"),
    ("Structured Output", "structured_output"),
    ("Role-based", "role_based"),
)

# All strategies compared side-by-side on the Interview Questions tab (same inputs, one question each).
COMPARE_PROMPT_STRATEGY_KEYS: tuple[str, ...] = (
    "zero_shot",
    "few_shot",
    "chain_of_thought",
    "structured_output",
    "role_based",
)


def prompt_strategy_key_from_label(label: str) -> str:
    """Map sidebar label to internal strategy key; unknown labels fall back to zero-shot."""
    for lbl, key in PROMPT_STRATEGY_OPTIONS:
        if lbl == label:
            return key
    return "zero_shot"


def label_for_prompt_strategy(key: str) -> str:
    """Human-readable label for pills and captions."""
    for lbl, k in PROMPT_STRATEGY_OPTIONS:
        if k == key:
            return lbl
    return key


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
