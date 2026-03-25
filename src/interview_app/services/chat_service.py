"""Mock interview chat orchestration (interviewer persona, FSM, LLM calls).

Routes each user turn through an explicit interview state machine and
``detect_user_turn_type`` so clarification, meta, and control turns never reach the
evaluator. Evaluation runs only in ``WAITING_FOR_ANSWER`` when the turn is classified
as ``ANSWER``.

Mutates ``session_state`` mock keys when provided, including ``ia_interview_state``,
``ia_mock_pending_question``, ``ia_candidate_topics``.
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
    InterviewState,
    MockInterviewPhase,
    UserMessageKind,
    UserTurnType,
    append_candidate_topics,
    build_interviewer_prompt,
    classify_user_message,
    clear_mock_interview_runtime_state,
    detect_user_turn_type,
    extract_candidate_topics,
    generate_contextual_follow_up_hints,
    get_candidate_topics,
    get_interview_state,
    get_pending_question,
    infer_focus_override_from_message,
    init_mock_interview_runtime_state,
    set_interview_state,
    set_mock_state,
    should_run_full_evaluation,
)
from interview_app.utils.errors import safe_user_message
from interview_app.utils.interview_question_output import first_question_text_from_output
from interview_app.utils.types import ChatMessage, EvaluationResult


@dataclass(frozen=True)
class MockInterviewLLMConfig:
    """Single source of sidebar LLM parameters for all mock-interview model calls."""

    model_preset: str
    resolved_model_name: str
    temperature: float
    top_p: float | None
    max_tokens: int


def mock_llm_config_from_settings(settings: UISettings) -> MockInterviewLLMConfig:
    preset = settings.model_preset
    cfg = get_model_config(preset)
    return MockInterviewLLMConfig(
        model_preset=preset,
        resolved_model_name=cfg.name,
        temperature=settings.temperature,
        top_p=settings.top_p,
        max_tokens=settings.max_tokens,
    )


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
    Run one interviewer turn. ``messages`` must already include the latest user message.

    When ``session_state`` is provided, updates mock interview keys for evaluation gating.
    """
    llm_cfg = mock_llm_config_from_settings(settings)

    if session_state is not None:
        init_mock_interview_runtime_state(session_state)

    if not messages:
        if session_state is not None:
            clear_mock_interview_runtime_state(session_state)
        return ChatTurnResult(
            assistant_message=(
                "Hello — when you are ready, say you’re ready for the interview to begin. "
                "I’ll ask the first question right after a brief intro."
            ),
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
    interview_state = get_interview_state(session_state)
    turn_type = detect_user_turn_type(last_user_content, pending_question=pending)
    kind = classify_user_message(last_user_content, pending_question=pending)

    if kind == UserMessageKind.RESTART_REQUEST:
        clear_mock_interview_runtime_state(session_state)
        return _greeting_and_first_question(
            settings,
            messages,
            llm_cfg,
            session_state=session_state,
            openai_api_key=openai_api_key,
            restart_ack="Starting fresh — here’s a new opening question.",
        )

    assistant_count = sum(1 for m in messages if m.role == "assistant")

    if assistant_count == 0:
        if turn_type == UserTurnType.GREETING or _looks_like_job_context(last_user_content):
            return _greeting_and_first_question(
                settings,
                messages,
                llm_cfg,
                session_state=session_state,
                openai_api_key=openai_api_key,
            )
        return _answer_general_question(
            settings, messages, last_user_content, llm_cfg, openai_api_key=openai_api_key
        )

    if should_run_full_evaluation(
        pending_question=pending,
        turn_type=turn_type,
        interview_state=interview_state,
        user_text=last_user_content,
    ):
        q = pending or ""
        return _evaluate_and_follow_up(
            settings,
            messages,
            last_user_content,
            interview_question=q,
            llm_cfg=llm_cfg,
            session_state=session_state,
            openai_api_key=openai_api_key,
        )

    if turn_type == UserTurnType.CONTROL:
        return _handle_control_instruction(
            settings,
            messages,
            last_user_content,
            llm_cfg,
            pending_question=pending,
            session_state=session_state,
            openai_api_key=openai_api_key,
        )

    if turn_type == UserTurnType.GREETING:
        return _generate_next_question_turn(
            settings,
            messages,
            llm_cfg,
            session_state=session_state,
            openai_api_key=openai_api_key,
            lead_in="Absolutely — here’s the next question.",
        )

    if pending and turn_type in (
        UserTurnType.CLARIFICATION,
        UserTurnType.META,
        UserTurnType.EXPERIENCE,
    ):
        if session_state is not None:
            set_interview_state(session_state, InterviewState.META_CONVERSATION)
        out = _interviewer_clarification_or_meta_turn(
            settings,
            messages,
            last_user_content,
            llm_cfg,
            pending_question=pending,
            session_state=session_state,
            openai_api_key=openai_api_key,
        )
        if session_state is not None:
            set_interview_state(session_state, InterviewState.WAITING_FOR_ANSWER)
        return out

    return _answer_general_question(
        settings, messages, last_user_content, llm_cfg, openai_api_key=openai_api_key
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
    llm_cfg: MockInterviewLLMConfig,
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
    lead_in: str | None = None,
    interview_focus: str | None = None,
) -> ChatTurnResult:
    """Generate one interview question; store canonical question text in session."""
    if session_state is not None:
        set_interview_state(session_state, InterviewState.ASKING_QUESTION)
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
        model=llm_cfg.model_preset,
        temperature=llm_cfg.temperature,
        top_p=llm_cfg.top_p,
        max_tokens=llm_cfg.max_tokens,
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
        interview_state=InterviewState.WAITING_FOR_ANSWER,
    )
    return ChatTurnResult(assistant_message=display, evaluation=None)


def _greeting_and_first_question(
    settings: UISettings,
    messages: list[ChatMessage],
    llm_cfg: MockInterviewLLMConfig,
    *,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
    restart_ack: str | None = None,
) -> ChatTurnResult:
    """Brief interviewer intro + structure + first question (intro is not graded)."""
    ok_title, _ = validate_role_title(settings.role_title)
    if not ok_title:
        return ChatTurnResult(
            assistant_message=(
                "Hi — set a **role title** in the sidebar to begin; then tell me you’re ready "
                "and I’ll open with structure plus your first question."
            ),
            evaluation=None,
        )
    role = (settings.role_title or "").strip() or "your target"
    if restart_ack:
        lead = (
            f"{restart_ack}\n\n"
            f"Hello — I’m conducting a mock interview for **{role}**. "
            "We’ll go one question at a time, I’ll give short feedback after each answer, then a follow-up. "
            "Here’s your first question."
        )
    else:
        lead = (
            f"Hello — I’m your interviewer today for **{role}**. "
            "We’ll go one question at a time: you answer, I share brief feedback, then the next question. "
            "Here’s your first question."
        )
    return _generate_next_question_turn(
        settings,
        messages,
        llm_cfg,
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
    llm_cfg: MockInterviewLLMConfig,
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
    ack = f"Understood — I’ll emphasize **{ack_focus}** in the next question."
    return _generate_next_question_turn(
        settings,
        messages,
        llm_cfg,
        session_state=session_state,
        openai_api_key=openai_api_key,
        lead_in=ack,
        interview_focus=override if override is not None else settings.interview_focus,
    )


def _interviewer_clarification_or_meta_turn(
    settings: UISettings,
    messages: list[ChatMessage],
    last_user_content: str,
    llm_cfg: MockInterviewLLMConfig,
    *,
    pending_question: str,
    session_state: dict[str, Any] | None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """In-character reply for clarification / meta / experience digression (no scoring)."""
    topics = get_candidate_topics(session_state)
    system = protect_system_prompt(
        build_interviewer_prompt(
            settings.persona,
            interview_round=settings.interview_round,
            focus=settings.interview_focus,
            role_title=(settings.role_title or "").strip() or "candidate role",
            seniority=settings.seniority,
            pending_question=pending_question,
            candidate_topics=topics,
        )
    )
    try:
        client = LLMClient(
            model=llm_cfg.resolved_model_name,
            temperature=min(0.85, llm_cfg.temperature + 0.15),
            max_tokens=min(500, max(220, llm_cfg.max_tokens // 2)),
            top_p=llm_cfg.top_p,
            api_key=openai_api_key,
        )
        extra = [{"role": m.role, "content": m.content} for m in messages[:-1]][-8:]
        resp = client.generate_response(
            system_prompt=system,
            user_prompt=last_user_content,
            model=llm_cfg.resolved_model_name,
            temperature=min(0.85, llm_cfg.temperature + 0.15),
            max_tokens=min(500, max(220, llm_cfg.max_tokens // 2)),
            top_p=llm_cfg.top_p,
            extra_messages=extra if extra else None,
            llm_route="mock_interview_meta",
        )
        out = run_output_pipeline(resp.text, service="chat_service")
        if not out.safe:
            return ChatTurnResult(
                assistant_message=out.reason
                or "I couldn’t respond to that just now — here’s the question again when you’re ready.\n\n"
                f"**Question:** {pending_question}",
                evaluation=None,
            )
        body = (out.text or "").strip()
        suffix = f"\n\n**Question:** {pending_question}"
        if pending_question and pending_question not in body:
            return ChatTurnResult(assistant_message=f"{body}{suffix}", evaluation=None)
        return ChatTurnResult(assistant_message=body or suffix.strip(), evaluation=None)
    except Exception as exc:
        return ChatTurnResult(
            assistant_message=(
                f"{safe_user_message(exc)}\n\n**Question:** {pending_question}"
            ),
            evaluation=None,
        )


def _answer_general_question(
    settings: UISettings,
    messages: list[ChatMessage],
    last_user_content: str,
    llm_cfg: MockInterviewLLMConfig,
    *,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """Fallback conversational turn (still uses sidebar LLM parameters)."""
    role = (settings.role_title or "").strip() or "your target"
    system = (
        "You are a concise assistant inside a mock interview app. The user’s message is not a graded "
        "interview answer. Reply helpfully in under 120 words, then invite them to say they’re ready "
        f"to continue the **{role}** mock interview."
    )
    system_prompt = protect_system_prompt(system)
    try:
        client = LLMClient(
            model=llm_cfg.resolved_model_name,
            temperature=min(0.7, llm_cfg.temperature + 0.2),
            max_tokens=min(400, llm_cfg.max_tokens),
            top_p=llm_cfg.top_p,
            api_key=openai_api_key,
        )
        extra = [{"role": m.role, "content": m.content} for m in messages[:-1]][-6:]
        resp = client.generate_response(
            system_prompt=system_prompt,
            user_prompt=last_user_content,
            model=llm_cfg.resolved_model_name,
            temperature=min(0.7, llm_cfg.temperature + 0.2),
            max_tokens=min(400, llm_cfg.max_tokens),
            top_p=llm_cfg.top_p,
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
            "I’m here to help. When you’re ready, say you’re ready to continue the mock interview."
        )
        return ChatTurnResult(assistant_message=text, evaluation=None)
    except Exception as exc:
        return ChatTurnResult(
            assistant_message=f"{safe_user_message(exc)} You can continue when you’re ready.",
            evaluation=None,
        )


def _format_evaluation_markdown(ev: EvaluationResult) -> str:
    """Readable markdown aligned with the professional evaluation schema."""
    lines: list[str] = ["## Overall Score", f"**{ev.score}/10**"]
    if (ev.technical_accuracy or "").strip():
        lines.extend(["", "## Technical Accuracy", ev.technical_accuracy.strip()])
    if (ev.clarity or "").strip():
        lines.extend(["", "## Clarity", ev.clarity.strip()])
    if (ev.depth or "").strip():
        lines.extend(["", "## Depth", ev.depth.strip()])
    if (ev.communication or "").strip():
        lines.extend(["", "## Communication", ev.communication.strip()])
    strengths = ev.strengths or ev.criteria_met
    improvements = ev.improvements or ev.criteria_missing
    if strengths:
        lines.extend(["", "## Strengths"])
        lines.extend(f"- {s}" for s in strengths[:8])
    if improvements:
        lines.extend(["", "## Improvements"])
        lines.extend(f"- {s}" for s in improvements[:8])
    if (ev.critique or "").strip():
        lines.extend(["", "## Critique", ev.critique.strip()])
    if (ev.improved_answer or "").strip():
        lines.extend(["", "## Better / Model Answer", ev.improved_answer.strip()])
    next_q = (ev.next_follow_up_question or (ev.follow_ups[0] if ev.follow_ups else "")).strip()
    if next_q:
        lines.extend(["", "## Next Follow-up Question", next_q])
    return "\n".join(lines).strip()


def _evaluate_and_follow_up(
    settings: UISettings,
    messages: list[ChatMessage],
    last_user_content: str,
    *,
    interview_question: str,
    llm_cfg: MockInterviewLLMConfig,
    session_state: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
) -> ChatTurnResult:
    """Evaluate the user's answer and return structured feedback plus one follow-up question."""
    fresh_topics = extract_candidate_topics(last_user_content)
    append_candidate_topics(session_state, fresh_topics)
    merged_topics = get_candidate_topics(session_state)
    role = (settings.role_title or "").strip() or "your role"
    hints = generate_contextual_follow_up_hints(
        merged_topics,
        role=role,
        seniority=settings.seniority,
        focus=settings.interview_focus,
    )
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
        model=llm_cfg.model_preset,
        temperature=llm_cfg.temperature,
        top_p=llm_cfg.top_p,
        max_tokens=llm_cfg.max_tokens,
        response_language=settings.response_language,
        persona=settings.persona,
        prompt_strategy=settings.prompt_strategy,
        candidate_topics=merged_topics,
        evaluation_context_hints=hints,
        session_state=session_state,
        skip_session_rate_limit=True,
        openai_api_key=openai_api_key,
    )

    if not eval_result.ok or eval_result.response is None:
        return ChatTurnResult(
            assistant_message=eval_result.error
            or "Evaluation failed. You can try answering again or ask for the next question.",
            evaluation=None,
        )

    ev = eval_result.evaluation
    if not ev:
        return ChatTurnResult(
            assistant_message=eval_result.response.text
            or "Evaluation complete. Ready for the next question when you are.",
            evaluation=None,
        )

    next_pending = (
        (ev.next_follow_up_question or (ev.follow_ups[0] if ev.follow_ups else "") or "").strip() or None
    )

    set_mock_state(
        session_state,
        pending_question=next_pending,
        phase=MockInterviewPhase.AWAITING_ANSWER if next_pending else MockInterviewPhase.FEEDBACK_GIVEN,
        interview_state=InterviewState.WAITING_FOR_ANSWER if next_pending else InterviewState.GREETING,
    )

    return ChatTurnResult(
        assistant_message=_format_evaluation_markdown(ev),
        evaluation=ev,
    )
