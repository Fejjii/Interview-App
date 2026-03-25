"""Mock interview conversation state and user-turn classification.

Tracks whether a real interview question is pending and classifies user text so
starters and controls are never sent to the answer evaluator.
"""

from __future__ import annotations

import re
from collections.abc import MutableMapping
from enum import Enum
from typing import Any

from interview_app.utils.types import ChatMessage

# Streamlit / in-memory session keys (also used with plain dicts in tests).
KEY_MOCK_PHASE = "ia_mock_phase"
KEY_PENDING_QUESTION = "ia_mock_pending_question"


class MockInterviewPhase(str, Enum):
    """High-level mock interview progress (persisted in session)."""

    NOT_STARTED = "not_started"
    INTERVIEW_STARTED = "interview_started"
    QUESTION_ASKED = "question_asked"
    AWAITING_ANSWER = "awaiting_answer"
    ANSWER_RECEIVED = "answer_received"
    FEEDBACK_GIVEN = "feedback_given"


class UserMessageKind(str, Enum):
    """Classification for the latest user message in mock interview."""

    GREETING = "greeting"
    START_REQUEST = "start_request"
    CONTROL_INSTRUCTION = "control_instruction"
    CLARIFICATION = "clarification"
    CANDIDATE_ANSWER = "candidate_answer"
    RESTART_REQUEST = "restart_request"
    OTHER = "other"


def clear_mock_interview_runtime_state(session_state: MutableMapping[str, Any] | None) -> None:
    """Reset FSM keys (no-op if session_state is None)."""
    if session_state is None:
        return
    session_state[KEY_MOCK_PHASE] = MockInterviewPhase.NOT_STARTED.value
    session_state[KEY_PENDING_QUESTION] = None


def init_mock_interview_runtime_state(session_state: MutableMapping[str, Any]) -> None:
    """Ensure keys exist (idempotent)."""
    session_state.setdefault(KEY_MOCK_PHASE, MockInterviewPhase.NOT_STARTED.value)
    if KEY_PENDING_QUESTION not in session_state:
        session_state[KEY_PENDING_QUESTION] = None


def get_pending_question(session_state: MutableMapping[str, Any] | None) -> str | None:
    if not session_state:
        return None
    q = session_state.get(KEY_PENDING_QUESTION)
    if q is None:
        return None
    s = str(q).strip()
    return s or None


def set_mock_state(
    session_state: MutableMapping[str, Any] | None,
    *,
    pending_question: str | None,
    phase: MockInterviewPhase,
) -> None:
    if session_state is None:
        return
    session_state[KEY_PENDING_QUESTION] = pending_question
    session_state[KEY_MOCK_PHASE] = phase.value


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _is_greeting(t: str) -> bool:
    if len(t) > 60:
        return False
    greetings = (
        "hi",
        "hey",
        "hello",
        "hi there",
        "hey there",
        "hello there",
        "hola",
        "yo",
        "sup",
        "howdy",
        "good morning",
        "good afternoon",
        "good evening",
    )
    core = t.rstrip("!?.")
    return core in greetings or t in greetings


def _is_restart_request(t: str) -> bool:
    phrases = (
        "new chat",
        "restart",
        "start over",
        "reset interview",
        "reset the interview",
        "clear chat",
        "begin again",
    )
    return any(p in t for p in phrases)


def _is_start_request(t: str) -> bool:
    phrases = (
        "let's start",
        "lets start",
        "start interview",
        "start the interview",
        "start a mock interview",
        "mock interview",
        "begin interview",
        "i'm ready",
        "im ready",
        "ready to start",
        "next question",
        "ask me a question",
        "ask the first question",
        "first question",
        "continue interview",
        "continue the interview",
    )
    return any(p in t for p in phrases)


def _is_clarification(t: str) -> bool:
    phrases = (
        "what do you mean",
        "can you clarify",
        "i don't understand",
        "dont understand",
        "unclear",
        "explain that",
        "say more about",
    )
    return any(p in t for p in phrases)


def _is_control_instruction(t: str) -> bool:
    if _is_restart_request(t):
        return False
    phrases = (
        "switch to ",
        "change to ",
        "focus on ",
        "let's focus",
        "lets focus",
        "only ask",
        "more behavioral",
        "more technical",
        "repeat the question",
        "say the question again",
        "ask a different",
        "another question",
        "skip this",
        "skip that",
        "new question",
        "different question",
        "can we switch",
        "could we switch",
    )
    return any(p in t for p in phrases)


def classify_user_message(text: str) -> UserMessageKind:
    """Classify the user's latest mock-interview message."""
    t = _norm(text)
    if not t:
        return UserMessageKind.OTHER
    if _is_restart_request(t):
        return UserMessageKind.RESTART_REQUEST
    if _is_greeting(t):
        return UserMessageKind.GREETING
    if _is_start_request(t):
        return UserMessageKind.START_REQUEST
    if _is_clarification(t):
        return UserMessageKind.CLARIFICATION
    if _is_control_instruction(t):
        return UserMessageKind.CONTROL_INSTRUCTION
    if _looks_like_interview_answer(text):
        return UserMessageKind.CANDIDATE_ANSWER
    return UserMessageKind.OTHER


def _looks_like_interview_answer(text: str) -> bool:
    t = (text or "").strip().lower()
    words = t.split()
    if len(words) >= 20 and "?" not in t:
        return True
    evidence_markers = (
        "i built",
        "i designed",
        "i implemented",
        "in my",
        "for example",
        "we used",
        "we implemented",
        "the trade-off",
        "the approach",
        "i would",
        "i'd approach",
    )
    if len(words) >= 10 and any(marker in t for marker in evidence_markers):
        return True
    return False


def _looks_like_general_question(text: str) -> bool:
    """True if the user message is small talk or a meta-question, not an answer."""
    t = (text or "").strip()
    if len(t) > 400:
        return False
    t_norm = _norm(t)
    question_starts = (
        "tell me ",
        "what is ",
        "what are ",
        "how does ",
        "how do ",
        "why ",
        "explain ",
        "can you ",
        "could you ",
        "tell me more ",
        "when ",
        "where ",
        "who ",
    )
    if t_norm.endswith("?") or any(t_norm.startswith(s) for s in question_starts):
        return True
    if "?" in t and len(t) < 150:
        return True
    social_phrases = (
        "how are you",
        "how's it going",
        "what's up",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "sounds good",
    )
    if any(p in t_norm for p in social_phrases):
        return True
    if len(t_norm.split()) <= 5:
        return True
    return False


def should_run_evaluation(
    *,
    pending_question: str | None,
    kind: UserMessageKind,
    user_text: str,
) -> bool:
    """
    Evaluation only when a real question is pending and the user turn is an answer.

    Starters, controls, greetings, and clarifications never evaluate.
    """
    if not (pending_question and pending_question.strip()):
        return False
    if kind in {
        UserMessageKind.GREETING,
        UserMessageKind.START_REQUEST,
        UserMessageKind.CONTROL_INSTRUCTION,
        UserMessageKind.CLARIFICATION,
        UserMessageKind.RESTART_REQUEST,
    }:
        return False
    if kind == UserMessageKind.CANDIDATE_ANSWER:
        return True
    # OTHER: short / meta → skip
    if _looks_like_general_question(user_text):
        return False
    t = _norm(user_text)
    if len(t.split()) < 8:
        return False
    return True


def infer_focus_override_from_message(text: str) -> str | None:
    """
    Map common user phrases to a catalog focus label (approximate sidebar values).

    Returns None if no recognized switch (e.g. only "repeat").
    """
    t = _norm(text)
    mapping: tuple[tuple[str, str], ...] = (
        ("behavioral", "Behavioral / Soft Skills"),
        ("soft skill", "Behavioral / Soft Skills"),
        ("technical knowledge", "Technical Knowledge"),
        ("technical", "Technical Knowledge"),
        ("coding", "Coding / Practical Exercise"),
        ("system design", "System Design / Architecture"),
        ("architecture", "System Design / Architecture"),
        ("leadership", "Leadership / Management"),
        ("culture", "Culture Fit / Values"),
        ("cv ", "CV / Experience Deep Dive"),
        ("experience deep", "CV / Experience Deep Dive"),
        ("case study", "Business Case / Strategy"),
        ("strategy", "Business Case / Strategy"),
        ("stakeholder", "Stakeholder Management"),
        ("negotiation", "Salary / Negotiation Preparation"),
    )
    for needle, focus in mapping:
        if needle in t:
            return focus
    return None


def extract_follow_up_from_feedback_message(assistant_text: str) -> str | None:
    """Parse the first follow-up line from mock-interview feedback formatting."""
    text = (assistant_text or "").strip()
    if not text:
        return None
    if "**Score:" not in text and not re.search(r"(?m)^##\s*score\s*$", text, re.IGNORECASE):
        # Heuristic: not our feedback layout
        if "Score:" not in text:
            return None
    # **Follow-up:**\nline — primary path from chat_service
    m = re.search(
        r"\*\*Follow-up:\*\*\s*\n+\s*(.+?)(?:\n\n|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        line = m.group(1).strip()
        return line or None
    m2 = re.search(r"(?mi)^##\s*Follow-up\s*\n+(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    if m2:
        block = m2.group(1).strip()
        first = block.splitlines()[0].strip() if block else ""
        return first or None
    return None


def sync_mock_interview_session_from_messages(
    session_state: MutableMapping[str, Any] | None,
    messages: list[ChatMessage],
) -> None:
    """
    Rebuild pending question + phase from transcript (e.g. after loading a session).

    Best-effort: older transcripts may only have blended assistant text.
    """
    if session_state is None:
        return
    if not messages:
        clear_mock_interview_runtime_state(session_state)
        return

    last_assistant: str | None = None
    for m in reversed(messages):
        if m.role == "assistant":
            last_assistant = m.content
            break
    if not last_assistant:
        clear_mock_interview_runtime_state(session_state)
        return

    fu = extract_follow_up_from_feedback_message(last_assistant)
    if fu:
        set_mock_state(session_state, pending_question=fu, phase=MockInterviewPhase.AWAITING_ANSWER)
        return

    if "**Score:" in last_assistant or re.search(r"(?m)^##\s*(Score|score)\s*$", last_assistant):
        set_mock_state(session_state, pending_question=None, phase=MockInterviewPhase.FEEDBACK_GIVEN)
        return

    pending = last_assistant.strip()
    set_mock_state(session_state, pending_question=pending, phase=MockInterviewPhase.AWAITING_ANSWER)
