"""Mock interview chat orchestration (coach turns, intent routing, LLM calls).

Consumes ``UISettings`` and chat history as ``ChatMessage`` list; runs the latest
user message through ``run_input_pipeline``, then dispatches to
``interview_generator`` or ``answer_evaluator`` depending on greeting vs
interview vs follow-up intent.

Outputs ``ChatTurnResult`` (assistant text plus optional ``EvaluationResult``).
Mutates nothing directly—callers pass ``session_state`` for rate limiting.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from interview_app.app.ui_settings import UISettings
from interview_app.llm.model_settings import get_model_config
from interview_app.llm.openai_client import LLMClient
from interview_app.security.guards import protect_system_prompt
from interview_app.security.pipeline import run_input_pipeline, run_output_pipeline
from interview_app.services.answer_evaluator import evaluate_answer
from interview_app.services.interview_generator import generate_questions
from interview_app.utils.errors import safe_user_message
from interview_app.utils.interview_question_output import first_question_text_from_output
from interview_app.utils.types import ChatMessage, EvaluationResult


@dataclass
class ChatTurnResult:
    """Result of one chat turn: assistant message and optional structured evaluation."""

    assistant_message: str
    evaluation: EvaluationResult | None = None


class TurnIntent(str, Enum):
    """Coarse intent buckets used to route each chat turn."""

    START_INTERVIEW = "start_interview"
    CONVERSATIONAL = "conversational"
    ANSWER_INTERVIEW = "answer_interview"


def run_turn(
    settings: UISettings,
    messages: list[ChatMessage],
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """
    Run one coach turn. ``messages`` must already include the latest user message.

    Routing:
    - Empty history: prompt the user to start.
    - No assistant messages yet: greeting, general Q&A, job context, or first question.
    - After assistant exists: infer intent (start interview, small talk, or answer evaluation + follow-up).

    Args:
        settings: Sidebar-derived configuration (role, persona, model, etc.).
        messages: Full transcript including the new user turn at the end.
        session_state: Streamlit session dict for rate limiting; optional.

    Returns:
        Assistant reply text and optional structured evaluation for the last answer.

    Side effects: none on ``messages``; may read rate-limit state via ``session_state``.
    """
    if not messages:
        return ChatTurnResult(
            assistant_message="Start the session by saying hello or asking for your first question.",
            evaluation=None,
        )

    last_user_content = ""
    for m in reversed(messages):
        if m.role == "user":
            last_user_content = m.content
            break

    # Run input pipeline on the latest user message (moderation + rate limit).
    input_check = run_input_pipeline(
        last_user_content,
        field_name="chat_message",
        session_state=session_state,
        check_rate=True,
        service="chat_service",
    )
    if not input_check.ok:
        return ChatTurnResult(
            assistant_message=input_check.error or "Your message could not be processed.",
            evaluation=None,
        )

    assistant_count = sum(1 for m in messages if m.role == "assistant")
    if assistant_count == 0:
        if _looks_like_explicit_start(last_user_content) or _looks_like_job_context(last_user_content):
            return _generate_next_question(
                settings, messages, session_state=session_state, openai_api_key=openai_api_key
            )
        if _looks_like_greeting(last_user_content):
            return _reply_to_greeting(settings, last_user_content)
        return _answer_general_question(settings, messages, last_user_content, openai_api_key=openai_api_key)

    intent = _infer_follow_up_intent(last_user_content)
    if intent is TurnIntent.START_INTERVIEW:
        return _generate_next_question(
            settings, messages, session_state=session_state, openai_api_key=openai_api_key
        )
    if intent is TurnIntent.CONVERSATIONAL:
        return _answer_general_question(settings, messages, last_user_content, openai_api_key=openai_api_key)

    return _evaluate_and_follow_up(
        settings, messages, last_user_content, session_state=session_state, openai_api_key=openai_api_key
    )


def _resolve_job_description_for_chat(
    settings: UISettings,
    messages: list[ChatMessage],
) -> str:
    """Prefer sidebar job description; otherwise reuse chat text as context."""
    jd = (settings.job_description or "").strip()
    if jd:
        return jd
    for m in messages:
        if m.role == "user" and m.content and "job" in m.content.lower():
            return m.content
    if messages:
        for m in reversed(messages):
            if m.role == "user" and m.content:
                return m.content
    return ""


def _generate_next_question(
    settings: UISettings,
    messages: list[ChatMessage],
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """Generate a single next question (first or after a follow-up)."""
    job_description = _resolve_job_description_for_chat(settings, messages)

    result = generate_questions(
        role_category=settings.role_category,
        role_title=settings.role_title,
        seniority=settings.seniority,
        interview_round=settings.interview_round,
        interview_focus=settings.interview_focus,
        job_description=job_description or "(none)",
        n_questions=1,
        prompt_strategy=settings.prompt_strategy,
        model=settings.model_preset,
        temperature=settings.temperature,
        top_p=settings.top_p,
        max_tokens=settings.max_tokens,
        response_language=settings.response_language,
        difficulty=settings.effective_question_difficulty,
        persona=settings.persona,
        session_state=session_state,
        skip_session_rate_limit=True,
        openai_api_key=openai_api_key,
    )

    if not result.ok or result.response is None:
        return ChatTurnResult(
            assistant_message=result.error or "Could not generate a question. Please try again.",
            evaluation=None,
        )

    text = (result.response.text or "").strip()
    json_first = first_question_text_from_output(text)
    if json_first:
        return ChatTurnResult(assistant_message=json_first, evaluation=None)
    # Extract first question if model returned a list
    if text:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for line in lines:
            if line[0:1].isdigit() and (")" in line or "." in line):
                idx = line.find(")") if ")" in line else line.find(".")
                if idx > 0:
                    text = line[idx + 1 :].strip()
                    break
            elif not line.lower().startswith("question") and len(line) > 20:
                text = line
                break
    return ChatTurnResult(assistant_message=text or result.response.text, evaluation=None)


def _looks_like_greeting(text: str) -> bool:
    """True if the first user message is a short greeting, not job context or a request to start."""
    t = (text or "").strip().lower()
    if len(t) > 50:
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
    )
    return t in greetings or t.rstrip("!?.") in greetings


def _reply_to_greeting(settings: UISettings, user_msg: str) -> ChatTurnResult:
    """Return a friendly greeting and invite the user to start the interview."""
    role = (settings.role_title or "").strip() or "your target"
    return ChatTurnResult(
        assistant_message=(
            f"Hi — I'm your AI interview coach for **{role}** practice. "
            "When you're ready, say something like *\"Let's start\"* or *\"I'm ready\"* and I'll ask your first question."
        ),
        evaluation=None,
    )


def _looks_like_explicit_start(text: str) -> bool:
    """True when the user clearly asks to begin or continue interview mode."""
    t = (text or "").strip().lower()
    if not t:
        return False
    start_phrases = (
        "let's start",
        "lets start",
        "start interview",
        "start the interview",
        "begin interview",
        "i'm ready",
        "im ready",
        "ready to start",
        "next question",
        "ask me a question",
        "continue interview",
        "continue the interview",
    )
    return any(phrase in t for phrase in start_phrases)


def _looks_like_job_context(text: str) -> bool:
    """Detect first-turn role/job context that should trigger question generation."""
    t = (text or "").strip().lower()
    if len(t.split()) < 8:
        return False
    cues = ("job description", "role:", "position:", "responsibilities", "requirements", "hiring", "company")
    return any(c in t for c in cues)


def _looks_like_general_question(text: str) -> bool:
    """True if the user message looks like a general/social question rather than an interview answer."""
    import re
    t = (text or "").strip()
    if len(t) > 400:
        return False
    # Normalize whitespace for matching
    t_norm = re.sub(r"\s+", " ", t.lower())
    # Question-style phrases
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
    # Social/courtesy phrases - treat as conversation, not interview answer.
    social_phrases = (
        "how are you",
        "how are you doing",
        "how's it going",
        "how are things",
        "what's up",
        "whats up",
        "how do you do",
        "how have you been",
        "how's everything",
        "how's your day",
        "how's your day going",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "how are ya",
        "how ya doing",
    )
    if any(p in t_norm for p in social_phrases):
        return True
    # Very short utterances are usually conversational, not evaluable answers.
    if len(t_norm.split()) <= 5:
        return True
    return False


def _looks_like_interview_answer(text: str) -> bool:
    """Heuristic for candidate-style answers to a previous interview question."""
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
    )
    if len(words) >= 10 and any(marker in t for marker in evidence_markers):
        return True
    return False


def _infer_follow_up_intent(last_user_content: str) -> TurnIntent:
    """Infer whether the latest user turn should start/continue interview, discuss, or be graded."""
    if _looks_like_explicit_start(last_user_content):
        return TurnIntent.START_INTERVIEW
    if _looks_like_general_question(last_user_content):
        return TurnIntent.CONVERSATIONAL
    if _looks_like_interview_answer(last_user_content):
        return TurnIntent.ANSWER_INTERVIEW
    # Safer default: if unsure, keep conversation flowing instead of grading random text.
    return TurnIntent.CONVERSATIONAL


def _answer_general_question(
    settings: UISettings,
    messages: list[ChatMessage],
    last_user_content: str,
    *,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """Answer a general/conversational question and invite back to the interview."""
    role = (settings.role_title or "").strip() or "your target"
    system = (
        "You are a friendly assistant inside an AI Interview Coach app. The user asked a general or off-topic question "
        "(not an interview answer). Reply helpfully and briefly in a conversational tone, then invite them to continue "
        f"the practice interview for their **{role}** target role when they're ready. Keep the reply under 140 words."
    )
    system_prompt = protect_system_prompt(system)
    try:
        cfg = get_model_config(settings.model_preset)
        client = LLMClient(
            model=cfg.name,
            temperature=min(0.7, settings.temperature + 0.2),
            max_tokens=min(400, settings.max_tokens),
            top_p=settings.top_p,
            api_key=openai_api_key,
        )
        extra = [{"role": m.role, "content": m.content} for m in messages[:-1]][-6:]
        resp = client.generate_response(
            system_prompt=system_prompt,
            user_prompt=last_user_content,
            model=cfg.name,
            temperature=min(0.7, settings.temperature + 0.2),
            max_tokens=min(400, settings.max_tokens),
            top_p=settings.top_p,
            extra_messages=extra if extra else None,
            llm_route="chat_conversational",
        )
        out = run_output_pipeline(resp.text, service="chat_service")
        if not out.safe:
            return ChatTurnResult(
                assistant_message=out.reason
                or "The response could not be shown. Please try again or continue with your interview practice.",
                evaluation=None,
            )
        text = (out.text or "").strip() or (
            "I'm here to help. When you're ready, we can continue with the interview practice."
        )
        return ChatTurnResult(assistant_message=text, evaluation=None)
    except Exception as exc:
        return ChatTurnResult(
            assistant_message=f"{safe_user_message(exc)} You can continue with the interview by answering the last question.",
            evaluation=None,
        )


def _evaluate_and_follow_up(
    settings: UISettings,
    messages: list[ChatMessage],
    last_user_content: str,
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """Evaluate the user's answer and return feedback plus one follow-up question."""
    # Find the last assistant message (the question the user answered)
    last_question = ""
    for m in reversed(messages):
        if m.role == "assistant":
            last_question = m.content
            break

    eval_result = evaluate_answer(
        role_category=settings.role_category,
        role_title=settings.role_title,
        seniority=settings.seniority,
        interview_round=settings.interview_round,
        interview_focus=settings.interview_focus,
        effective_difficulty=settings.effective_question_difficulty,
        job_description=settings.job_description,
        question=last_question,
        answer=last_user_content,
        model=settings.model_preset,
        temperature=settings.temperature,
        top_p=settings.top_p,
        max_tokens=settings.max_tokens,
        response_language=settings.response_language,
        persona=settings.persona,
        session_state=session_state,
        skip_session_rate_limit=True,
        openai_api_key=openai_api_key,
    )

    if not eval_result.ok or eval_result.response is None:
        return ChatTurnResult(
            assistant_message=eval_result.error or "Evaluation failed. You can try answering again or ask for the next question.",
            evaluation=None,
        )

    parts = []
    ev = eval_result.evaluation
    if ev:
        parts.append(f"**Score: {ev.score}/10**")
        if ev.criteria_met:
            parts.append("**What you did well:**")
            for c in ev.criteria_met[:3]:
                parts.append(f"- {c}")
        if ev.criteria_missing:
            parts.append("**What to improve:**")
            for c in ev.criteria_missing[:3]:
                parts.append(f"- {c}")
        if ev.critique:
            parts.append(f"**Critique:** {ev.critique[:300]}{'…' if len(ev.critique) > 300 else ''}")
        if ev.follow_ups:
            follow_up = ev.follow_ups[0]
            parts.append("")
            parts.append("**Follow-up:**")
            parts.append(follow_up)
    else:
        parts.append(eval_result.response.text or "Evaluation complete. Ready for the next question when you are.")

    return ChatTurnResult(
        assistant_message="\n\n".join(parts),
        evaluation=ev,
    )
