"""Mock interview chat orchestration (coach turns, intent routing, LLM calls).

Routes each user turn through a small FSM plus message classification so greetings,
start requests, and control phrases never reach the answer evaluator. Only turns that
answer an explicit pending interview question are scored.

Mutates ``session_state`` mock keys when provided: ``ia_mock_phase``,
``ia_mock_pending_question``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interview_app.app.interview_form_config import validate_role_title
from interview_app.app.ui_settings import UISettings
from interview_app.llm.model_settings import get_model_config
from interview_app.llm.openai_client import LLMClient
from interview_app.security.guards import protect_system_prompt
from interview_app.security.pipeline import run_input_pipeline, run_output_pipeline
from interview_app.services.answer_evaluator import evaluate_answer
from interview_app.services.interview_generator import generate_questions
from interview_app.services.mock_interview_flow import (
    MockInterviewPhase,
    UserMessageKind,
    classify_user_message,
    clear_mock_interview_runtime_state,
    get_pending_question,
    infer_focus_override_from_message,
    init_mock_interview_runtime_state,
    set_mock_state,
    should_run_evaluation,
)
from interview_app.utils.errors import safe_user_message
from interview_app.utils.interview_question_output import first_question_text_from_output
from interview_app.utils.types import ChatMessage, EvaluationResult


@dataclass
class ChatTurnResult:
    """Result of one chat turn: assistant message and optional structured evaluation."""

    assistant_message: str
    evaluation: EvaluationResult | None = None


def run_turn(
    settings: UISettings,
    messages: list[ChatMessage],
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """
    Run one coach turn. ``messages`` must already include the latest user message.

    When ``session_state`` is provided, updates mock interview keys for evaluation gating.
    """
    if session_state is not None:
        init_mock_interview_runtime_state(session_state)

    if not messages:
        if session_state is not None:
            clear_mock_interview_runtime_state(session_state)
        return ChatTurnResult(
            assistant_message="Start the session by saying hello or asking for your first question.",
            evaluation=None,
        )

    last_user_content = ""
    for m in reversed(messages):
        if m.role == "user":
            last_user_content = m.content
            break

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

    pending = get_pending_question(session_state)
    kind = classify_user_message(last_user_content)

    if kind == UserMessageKind.RESTART_REQUEST:
        clear_mock_interview_runtime_state(session_state)
        return _greeting_and_first_question(
            settings,
            messages,
            session_state=session_state,
            openai_api_key=openai_api_key,
            restart_ack="Starting fresh — here's a new opening question.",
        )

    assistant_count = sum(1 for m in messages if m.role == "assistant")

    if assistant_count == 0:
        if kind in (UserMessageKind.GREETING, UserMessageKind.START_REQUEST):
            return _greeting_and_first_question(
                settings,
                messages,
                session_state=session_state,
                openai_api_key=openai_api_key,
            )
        if _looks_like_job_context(last_user_content):
            return _generate_next_question_turn(
                settings, messages, session_state=session_state, openai_api_key=openai_api_key
            )
        return _answer_general_question(
            settings, messages, last_user_content, openai_api_key=openai_api_key
        )

    if should_run_evaluation(pending_question=pending, kind=kind, user_text=last_user_content):
        q = pending or ""
        return _evaluate_and_follow_up(
            settings,
            messages,
            last_user_content,
            interview_question=q,
            session_state=session_state,
            openai_api_key=openai_api_key,
        )

    if kind == UserMessageKind.CONTROL_INSTRUCTION:
        return _handle_control_instruction(
            settings,
            messages,
            last_user_content,
            pending_question=pending,
            session_state=session_state,
            openai_api_key=openai_api_key,
        )

    if kind == UserMessageKind.START_REQUEST:
        return _generate_next_question_turn(
            settings,
            messages,
            session_state=session_state,
            openai_api_key=openai_api_key,
        )

    if pending and kind in (UserMessageKind.GREETING, UserMessageKind.CLARIFICATION):
        return ChatTurnResult(
            assistant_message=(
                "We're in the middle of a question — share your answer when you're ready, "
                "or type **repeat the question** if you need it repeated.\n\n"
                f"**Question:** {pending}"
            ),
            evaluation=None,
        )

    return _answer_general_question(
        settings, messages, last_user_content, openai_api_key=openai_api_key
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


def _normalize_question_text(text: str, raw_fallback: str) -> str:
    text = (text or "").strip()
    json_first = first_question_text_from_output(text)
    if json_first:
        return json_first.strip()
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
    return (text or raw_fallback).strip()


def _generate_next_question_turn(
    settings: UISettings,
    messages: list[ChatMessage],
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
    lead_in: str | None = None,
    interview_focus: str | None = None,
) -> ChatTurnResult:
    """Generate one interview question; store canonical question text in session."""
    ok_title, _ = validate_role_title(settings.role_title)
    if not ok_title:
        return ChatTurnResult(
            assistant_message=(
                "Please enter a **role title** in the sidebar so I can ask a realistic question."
            ),
            evaluation=None,
        )

    job_description = _resolve_job_description_for_chat(settings, messages)
    focus = settings.interview_focus if interview_focus is None else interview_focus

    result = generate_questions(
        role_category=settings.role_category,
        role_title=settings.role_title,
        seniority=settings.seniority,
        interview_round=settings.interview_round,
        interview_focus=focus,
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

    raw = (result.response.text or "").strip()
    question_text = _normalize_question_text(raw, raw_fallback=result.response.text or "")
    display = f"{lead_in}\n\n{question_text}" if lead_in else question_text
    set_mock_state(
        session_state,
        pending_question=question_text,
        phase=MockInterviewPhase.AWAITING_ANSWER,
    )
    return ChatTurnResult(assistant_message=display, evaluation=None)


def _greeting_and_first_question(
    settings: UISettings,
    messages: list[ChatMessage],
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
    restart_ack: str | None = None,
) -> ChatTurnResult:
    """Intro + first question in one assistant turn (intro does not become the graded 'question')."""
    ok_title, _ = validate_role_title(settings.role_title)
    if not ok_title:
        return ChatTurnResult(
            assistant_message=(
                "Hi! Set a **role title** in the sidebar to begin — then say hello or **Let's start** "
                "for your first question."
            ),
            evaluation=None,
        )
    role = (settings.role_title or "").strip() or "your target"
    if restart_ack:
        lead = f"{restart_ack}\n\nI'm your AI interview coach for **{role}** practice. Here's your next question."
    else:
        lead = (
            f"Hi — I'm your AI interview coach for **{role}** practice. "
            "I'll ask targeted questions based on your sidebar setup. Here's your first question."
        )
    return _generate_next_question_turn(
        settings,
        messages,
        session_state=session_state,
        openai_api_key=openai_api_key,
        lead_in=lead,
        interview_focus=settings.interview_focus,
    )


def _looks_like_job_context(text: str) -> bool:
    """Detect first-turn role/job context that should trigger question generation."""
    t = (text or "").strip().lower()
    if len(t.split()) < 8:
        return False
    cues = ("job description", "role:", "position:", "responsibilities", "requirements", "hiring", "company")
    return any(c in t for c in cues)


def _handle_control_instruction(
    settings: UISettings,
    messages: list[ChatMessage],
    last_user_content: str,
    *,
    pending_question: str | None,
    session_state: dict[str, Any] | None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """Repeat, focus switch, or fresh question — never triggers evaluation."""
    t = (last_user_content or "").strip().lower()
    if pending_question and any(
        p in t for p in ("repeat the question", "say the question again", "repeat question")
    ):
        return ChatTurnResult(
            assistant_message=f"Of course — here it is again:\n\n**Question:** {pending_question}",
            evaluation=None,
        )

    override = infer_focus_override_from_message(last_user_content)
    ack_focus = override or settings.interview_focus
    ack = f"Absolutely — I'll emphasize **{ack_focus}** in the next question."
    return _generate_next_question_turn(
        settings,
        messages,
        session_state=session_state,
        openai_api_key=openai_api_key,
        lead_in=ack,
        interview_focus=override if override is not None else settings.interview_focus,
    )


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
    interview_question: str,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """Evaluate the user's answer and return feedback plus one follow-up question."""
    eval_result = evaluate_answer(
        role_category=settings.role_category,
        role_title=settings.role_title,
        seniority=settings.seniority,
        interview_round=settings.interview_round,
        interview_focus=settings.interview_focus,
        effective_difficulty=settings.effective_question_difficulty,
        job_description=settings.job_description,
        question=interview_question,
        answer=last_user_content,
        model=settings.model_preset,
        temperature=settings.temperature,
        top_p=settings.top_p,
        max_tokens=settings.max_tokens,
        response_language=settings.response_language,
        persona=settings.persona,
        prompt_strategy=settings.prompt_strategy,
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
    next_pending: str | None = None
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
            next_pending = follow_up.strip() or None
            parts.append("")
            parts.append("**Follow-up:**")
            parts.append(follow_up)
    else:
        parts.append(eval_result.response.text or "Evaluation complete. Ready for the next question when you are.")

    set_mock_state(
        session_state,
        pending_question=next_pending,
        phase=MockInterviewPhase.AWAITING_ANSWER if next_pending else MockInterviewPhase.NOT_STARTED,
    )

    return ChatTurnResult(
        assistant_message="\n\n".join(parts),
        evaluation=ev,
    )
