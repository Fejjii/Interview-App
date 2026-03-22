"""
Streamlit main-area layout: compact header, configuration summary bar, workspace tabs.

Sidebar holds all configuration (`controls.render_sidebar_configuration`).
Main area: hero, summary pills, tabbed workspace (mock interview, questions, feedback).
"""

from __future__ import annotations

import streamlit as st

from interview_app.app.ui_settings import UISettings, WORKSPACE_TAB_LABELS
from interview_app.app.conversation_state import (
    append_message,
    clear_messages,
    get_messages,
    init_session_state,
    snapshot_meta_from_settings,
)
from interview_app.services.answer_evaluator import evaluate_answer
from interview_app.services.chat_service import run_turn as chat_run_turn
from interview_app.services.interview_generator import generate_questions
from interview_app.storage.sessions import save_session
from interview_app.ui.display import (
    show_error,
    show_evaluation_result,
    show_guardrail_summary,
    show_llm_response,
    show_prompt_debug,
    show_settings_debug,
)
from interview_app.ui.theme import render_configuration_pill_bar
from interview_app.app.interview_form_config import validate_role_title
from interview_app.ui.widgets import (
    answer_input,
    question_context_input,
)
from interview_app.utils.errors import safe_user_message
from interview_app.utils.language import DEFAULT_LANGUAGE, detect_language


def render_hero_header() -> None:
    """Compact page title and subtitle."""
    st.markdown(
        """
<div class="ia-hero ia-hero-compact" aria-label="Application header">
  <h1 class="ia-hero-title">AI Interview Preparation Assistant</h1>
  <p class="ia-hero-subtitle">Practice interviews tailored to your role, level, and stage—then review feedback and generated questions in one workspace.</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_main_content(settings: UISettings) -> None:
    """Workspace: summary bar + tabs (mock interview, questions, feedback)."""
    init_session_state()

    render_configuration_summary_bar(settings)

    tab_labels = list(WORKSPACE_TAB_LABELS)
    if "ia_workspace_tab" not in st.session_state:
        st.session_state.ia_workspace_tab = tab_labels[0]
    if st.session_state.ia_workspace_tab not in tab_labels:
        st.session_state.ia_workspace_tab = tab_labels[0]

    st.radio(
        "Workspace",
        tab_labels,
        horizontal=True,
        key="ia_workspace_tab",
        label_visibility="collapsed",
    )

    tab = st.session_state.ia_workspace_tab

    if tab == tab_labels[0]:
        _render_mock_interview_tab(settings)
    elif tab == tab_labels[1]:
        _render_question_generation_tab(settings)
    else:
        _render_answer_feedback_tab(settings)


def render_configuration_summary_bar(settings: UISettings) -> None:
    """Compact read-only strip of active setup (replaces the old right column)."""
    st.markdown(
        render_configuration_pill_bar(settings=settings),
        unsafe_allow_html=True,
    )


def _render_session_row_compact(settings: UISettings) -> None:
    """Session name, save, new—aligned row above chat."""
    messages = get_messages()
    session_id = st.session_state.get("current_session_id")
    status = "Saved" if session_id else ("In progress" if messages else "New session")

    c0, c1, c2, c3 = st.columns([2, 2, 1, 1])
    with c0:
        st.caption(f"**Session** · {status}")
    with c1:
        session_title = st.text_input(
            "Session name",
            placeholder="e.g. Backend practice",
            key="session_title",
            label_visibility="collapsed",
        )
    with c2:
        if st.button("Save", use_container_width=True, type="primary", key="main_save_session"):
            if not messages:
                st.warning("No messages to save yet.")
            else:
                meta = snapshot_meta_from_settings(
                    settings,
                    session_id,
                    title=session_title or "Untitled session",
                )
                msgs = [{"role": m.role, "content": m.content} for m in messages]
                sid = save_session(
                    session_id,
                    meta,
                    msgs,
                    title=session_title or "Untitled session",
                )
                st.session_state.current_session_id = sid
                st.toast(f"Saved as \"{session_title or 'Untitled'}\"")
                st.rerun()
    with c3:
        if st.button("New chat", use_container_width=True, key="main_new_session"):
            clear_messages()
            st.session_state.current_session_id = None
            st.session_state.session_meta = None
            st.rerun()


def _render_mock_interview_tab(settings: UISettings) -> None:
    """Primary workspace: session row + wide chat."""
    st.markdown("##### Mock interview")
    st.caption(
        "Answer as you would live. The coach uses your sidebar configuration and adapts each turn."
    )

    with st.expander("How to use", expanded=False):
        st.markdown(
            "Type a greeting or **Let's start** for your first question. "
            "After each answer you get brief feedback and a follow-up. "
            "Adjust role and round in the sidebar anytime."
        )

    _render_session_row_compact(settings)

    messages = get_messages()
    chat_container = st.container()
    with chat_container:
        if not messages:
            st.info(
                "Say hello, paste a short role summary, or type **Let's start** when you are ready for your first question."
            )
        else:
            for msg in messages:
                with st.chat_message(msg.role):
                    st.markdown(msg.content)

    if prompt := st.chat_input("Your answer or message"):
        if st.session_state.get("response_language") is None and prompt.strip():
            st.session_state.response_language = detect_language(prompt)
        append_message("user", prompt)
        with st.spinner("Thinking…"):
            try:
                updated = get_messages()
                result = chat_run_turn(
                    settings, updated, session_state=dict(st.session_state)
                )
                append_message("assistant", result.assistant_message)
            except Exception as exc:
                msg = safe_user_message(exc)
                append_message("assistant", f"Sorry, {msg}")
                show_error(title="Chat error", body=msg)
        st.rerun()

    if settings.show_debug:
        show_settings_debug(
            settings=settings, extra={"message_count": len(messages)}
        )


def _maybe_run_pending_generation(settings: UISettings) -> None:
    """Run question generation once after sidebar shortcut."""
    if not st.session_state.get("ia_pending_generate"):
        return
    st.session_state.ia_pending_generate = False

    ok_title, _ = validate_role_title(settings.role_title)
    if not ok_title:
        st.warning("Set a **role title** in the sidebar to generate questions.")
        return

    jd = settings.job_description or ""
    if st.session_state.get("response_language") is None and jd.strip():
        st.session_state.response_language = detect_language(jd)
    resolved_lang = st.session_state.get("response_language") or DEFAULT_LANGUAGE
    n_questions = int(st.session_state.get("ia_n_questions", 5))

    try:
        with st.spinner("Generating questions…"):
            gen_result = generate_questions(
                role_category=settings.role_category,
                role_title=settings.role_title,
                seniority=settings.seniority,
                interview_round=settings.interview_round,
                interview_focus=settings.interview_focus,
                job_description=jd,
                n_questions=n_questions,
                prompt_strategy=settings.prompt_strategy,
                model=settings.model_preset,
                temperature=settings.temperature,
                top_p=settings.top_p,
                max_tokens=settings.max_tokens,
                response_language=resolved_lang,
                difficulty=settings.effective_question_difficulty,
                persona=settings.persona,
                session_state=dict(st.session_state),
            )
    except Exception as exc:
        show_error(title="Generation failed", body=safe_user_message(exc))
        return

    show_guardrail_summary(guardrails=gen_result.guardrails)
    if not gen_result.ok or gen_result.response is None:
        show_error(
            title="Request blocked",
            body=gen_result.error or "Unknown error.",
        )
        return

    show_llm_response(
        title="Generated questions",
        response=gen_result.response,
        settings=settings,
        structured=True,
    )
    st.toast("Questions generated.")
    if settings.show_debug and gen_result.prompt is not None:
        show_prompt_debug(
            system_prompt=gen_result.prompt.system_prompt,
            user_prompt=gen_result.prompt.user_prompt,
        )


def _render_question_generation_tab(settings: UISettings) -> None:
    """Generate and display structured interview questions."""
    st.markdown("##### Interview questions")
    st.caption("Generate a focused set of prompts from your current sidebar configuration.")

    st.number_input(
        "Number of questions",
        min_value=1,
        max_value=20,
        value=int(st.session_state.get("ia_n_questions", 5)),
        step=1,
        help="How many distinct prompts to generate in one run.",
        key="ia_n_questions",
    )

    _maybe_run_pending_generation(settings)

    if st.button(
        "Generate interview questions",
        type="primary",
        use_container_width=True,
        key="btn_generate_questions",
    ):
        ok_title, _ = validate_role_title(settings.role_title)
        if not ok_title:
            st.warning("Set a **role title** in the sidebar.")
        else:
            st.session_state.ia_pending_generate = True
            st.rerun()

    if settings.show_debug:
        nq = int(st.session_state.get("ia_n_questions", 5))
        show_settings_debug(
            settings=settings,
            extra={
                "n_questions": nq,
                "job_description_len": len(settings.job_description or ""),
            },
        )


def _render_answer_feedback_tab(settings: UISettings) -> None:
    """Paste question + answer; show structured evaluation."""
    st.markdown("##### Feedback and evaluation")
    st.caption("Evaluate a single answer against your configured role and interview context.")

    question = question_context_input()
    answer = answer_input()

    if st.button(
        "Evaluate answer",
        type="primary",
        use_container_width=True,
        key="btn_evaluate_answer",
    ):
        ok_title, _ = validate_role_title(settings.role_title)
        if not ok_title:
            st.warning("Set a **role title** in the sidebar.")
        else:
            if st.session_state.get("response_language") is None and (
                question.strip() or answer.strip()
            ):
                st.session_state.response_language = detect_language(question or answer)
            resolved_lang = (
                st.session_state.get("response_language") or DEFAULT_LANGUAGE
            )
            try:
                with st.spinner("Evaluating answer…"):
                    eval_result = evaluate_answer(
                        role_category=settings.role_category,
                        role_title=settings.role_title,
                        seniority=settings.seniority,
                        interview_round=settings.interview_round,
                        interview_focus=settings.interview_focus,
                        effective_difficulty=settings.effective_question_difficulty,
                        job_description=settings.job_description,
                        question=question,
                        answer=answer,
                        model=settings.model_preset,
                        temperature=settings.temperature,
                        top_p=settings.top_p,
                        max_tokens=settings.max_tokens,
                        response_language=resolved_lang,
                        persona=settings.persona,
                        session_state=dict(st.session_state),
                    )
            except Exception as exc:
                show_error(title="Evaluation failed", body=safe_user_message(exc))
            else:
                show_guardrail_summary(guardrails=eval_result.guardrails)
                if not eval_result.ok or eval_result.response is None:
                    show_error(
                        title="Request blocked",
                        body=eval_result.error or "Unknown error.",
                    )
                else:
                    if eval_result.evaluation:
                        show_evaluation_result(eval_result.evaluation)
                        st.toast("Evaluation complete.")
                    else:
                        show_llm_response(
                            title="Evaluation", response=eval_result.response
                        )
                    if (
                        settings.show_debug
                        and eval_result.system_prompt
                        and eval_result.user_prompt
                    ):
                        show_prompt_debug(
                            system_prompt=eval_result.system_prompt,
                            user_prompt=eval_result.user_prompt,
                        )

    if settings.show_debug:
        show_settings_debug(
            settings=settings,
            extra={"question_len": len(question), "answer_len": len(answer)},
        )
