"""Session-level interview context for mock interviews (accumulated candidate signals).

Stores merged ``InterviewTopicsDict`` in Streamlit/session dicts. Used when generating
the next question so the model drills into the candidate's stated tools and projects
instead of generic behavioral prompts.
"""

from __future__ import annotations

import re
from collections.abc import MutableMapping
from typing import Any

from interview_app.utils.types import ChatMessage

from interview_app.services.context_extractor import (
    InterviewTopicsDict,
    empty_interview_topics,
    extract_interview_topics,
    flatten_interview_topics,
    interview_topics_non_empty,
)

KEY_SESSION_INTERVIEW_CONTEXT = "ia_session_interview_context"

# Caps keep prompts bounded; oldest entries naturally age out per bucket (merge truncates).
_MAX_PER_BUCKET = 32


def init_session_interview_context(session_state: MutableMapping[str, Any]) -> None:
    if KEY_SESSION_INTERVIEW_CONTEXT not in session_state:
        session_state[KEY_SESSION_INTERVIEW_CONTEXT] = empty_interview_topics()


def flatten_session_context_for_evaluator(session_state: MutableMapping[str, Any] | None) -> list[str]:
    """Flatten stored interview context into tag-like strings for answer evaluation."""
    return flatten_interview_topics(get_session_interview_context(session_state), max_items=40)


def rebuild_session_interview_context_from_transcript(
    session_state: MutableMapping[str, Any] | None,
    messages: list[ChatMessage],
) -> None:
    """Restore accumulated context after loading a saved session (best-effort)."""
    if session_state is None:
        return
    clear_session_interview_context(session_state)
    for m in messages:
        if m.role == "user" and (m.content or "").strip():
            merge_message_into_session_context(session_state, m.content)


def clear_session_interview_context(session_state: MutableMapping[str, Any] | None) -> None:
    if session_state is None:
        return
    session_state[KEY_SESSION_INTERVIEW_CONTEXT] = empty_interview_topics()


def get_session_interview_context(session_state: MutableMapping[str, Any] | None) -> InterviewTopicsDict:
    if not session_state:
        return empty_interview_topics()
    raw = session_state.get(KEY_SESSION_INTERVIEW_CONTEXT)
    if not isinstance(raw, dict):
        return empty_interview_topics()
    out = empty_interview_topics()
    for k in out:
        v = raw.get(k)
        if isinstance(v, list):
            out[k] = [str(x).strip() for x in v if str(x).strip()][: _MAX_PER_BUCKET]
    return out


def merge_message_into_session_context(
    session_state: MutableMapping[str, Any] | None,
    message: str,
) -> InterviewTopicsDict:
    """Parse ``message`` and union into stored context; returns the updated snapshot."""
    if session_state is None:
        return empty_interview_topics()
    init_session_interview_context(session_state)
    incoming = extract_interview_topics(message, max_per_bucket=_MAX_PER_BUCKET)
    current = get_session_interview_context(session_state)
    merged: InterviewTopicsDict = empty_interview_topics()
    for key in merged:
        seen: set[str] = set()
        combined: list[str] = []
        for item in list(current[key]) + list(incoming[key]):
            kl = item.strip().lower()
            if not kl or kl in seen:
                continue
            seen.add(kl)
            combined.append(item.strip())
            if len(combined) >= _MAX_PER_BUCKET:
                break
        merged[key] = combined
    session_state[KEY_SESSION_INTERVIEW_CONTEXT] = merged
    return merged


def context_summary_lines(ctx: InterviewTopicsDict) -> list[str]:
    """Human-readable lines for prompts (no markdown headers)."""
    lines: list[str] = []
    if ctx["tools"]:
        lines.append("Tools: " + ", ".join(ctx["tools"][:15]))
    if ctx["technologies"]:
        lines.append("Technologies: " + ", ".join(ctx["technologies"][:12]))
    if ctx["concepts"]:
        lines.append("Concepts: " + ", ".join(ctx["concepts"][:12]))
    if ctx["projects"]:
        lines.append("Projects / themes: " + ", ".join(ctx["projects"][:12]))
    if ctx["achievements"]:
        lines.append("Achievements / outcomes: " + ", ".join(ctx["achievements"][:10]))
    return lines


def format_context_for_question_prompt(ctx: InterviewTopicsDict) -> str:
    """Block appended to the question-generation user prompt when context applies."""
    if not interview_topics_non_empty(ctx):
        return ""
    lines = context_summary_lines(ctx)
    body = "\n".join(lines)
    return (
        "The candidate previously mentioned the following in this mock interview conversation:\n"
        f"{body}\n\n"
        "You are a technical interviewer. Generate the next question as a **deep technical follow-up** "
        "grounded in those specifics. Prefer angles such as: architecture, trade-offs, failure modes, "
        "debugging an incident, performance optimization, scaling, data quality, testing strategy, "
        "monitoring/observability, pipeline orchestration, and cost optimization — **not** a generic "
        "unrelated behavioral question unless there is no technical content above.\n"
        "Ask exactly one clear interview question."
    )


def user_requests_context_based_question(message: str) -> bool:
    """True when the user explicitly wants a follow-up tied to their prior story."""
    text_norm = re.sub(r"\s+", " ", (message or "").strip().lower())
    return _user_requests_context_question(text_norm)


def _user_requests_context_question(text_norm: str) -> bool:
    phrases = (
        "related to that",
        "related to this",
        "about that project",
        "about this project",
        "question related",
        "ask me a question related",
        "ask a question related",
        "ask me something about",
        "about what i said",
        "based on what i said",
        "based on my experience",
        "about my experience",
        "dig deeper",
        "drill into",
        "follow up on that",
        "follow-up on that",
        "something technical about",
    )
    return any(p in text_norm for p in phrases)


def _message_suggests_experience(text_norm: str) -> bool:
    markers = (
        "i built",
        "i implemented",
        "i designed",
        "i migrated",
        "we migrated",
        "we built",
        "in my last",
        "in my previous",
        "my team",
        "legacy",
        "production",
    )
    return any(m in text_norm for m in markers)


def should_use_context(
    user_message: str,
    session_state: MutableMapping[str, Any] | None,
) -> bool:
    """
    Whether mock-interview **question generation** should inject candidate context instructions.

    True when stored context is non-empty, the user explicitly asks for a related question,
    or the message looks like experience-sharing (already merged into context for this turn).
    """
    ctx = get_session_interview_context(session_state)
    text_norm = re.sub(r"\s+", " ", (user_message or "").strip().lower())

    if interview_topics_non_empty(ctx):
        return True
    if _user_requests_context_question(text_norm):
        return True
    if _message_suggests_experience(text_norm):
        return True
    return False


def build_question_generation_context_suffix(
    user_message: str,
    session_state: MutableMapping[str, Any] | None,
) -> str:
    """
    Extra user-prompt text for ``generate_questions`` during mock interview.

    When structured context exists, steers the model toward technical follow-ups.
    When the user explicitly asks for a related question but context is empty,
    asks for a technical deep-dive invite instead of a random behavioral item.
    """
    ctx = get_session_interview_context(session_state)
    text_norm = re.sub(r"\s+", " ", (user_message or "").strip().lower())
    if interview_topics_non_empty(ctx):
        return format_context_for_question_prompt(ctx)
    if _user_requests_context_question(text_norm):
        return (
            "The candidate asked for the **next question to relate to their recent project or prior answer**, "
            "but no structured tool/project list was captured yet.\n"
            "Ask **one** technical question that invites them to go deep on a concrete system they worked on "
            "(architecture, metrics, failures, testing, cost) - not a generic behavioral question."
        )
    return ""
