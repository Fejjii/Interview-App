"""
Streamlit main-area layout: header, configuration summary card, primary workspace navigation.

Sidebar holds all configuration (`controls.render_sidebar_configuration`).
Main area: hero, Current Setup card, segmented workspace nav (session `ia_workspace_tab`),
then the active panel (mock interview, questions, CV prep, feedback).
"""

from __future__ import annotations

import html
import json
from typing import Any

import streamlit as st

from interview_app.app import cv_session_state as cvs
from interview_app.app.usage_mode import openai_api_key_for_llm
from interview_app.app.conversation_state import (
    append_message,
    clear_messages,
    get_messages,
    init_session_state,
    snapshot_meta_from_settings,
)
from interview_app.app.interview_form_config import validate_role_title
from interview_app.app.ui_settings import (
    PROMPT_STRATEGY_OPTIONS,
    WORKSPACE_TAB_LABELS,
    UISettings,
    label_for_prompt_strategy,
    prompt_strategy_key_from_label,
)
from interview_app.cv.models import (
    CVAnalysisBundle,
    CVPracticeBundle,
    CVPracticeEvaluationBatch,
    CVStructuredExtraction,
)
from interview_app.services.answer_evaluator import evaluate_answer
from interview_app.services.chat_service import run_turn as chat_run_turn
from interview_app.services.cv_interview_service import (
    CVInterviewServiceResult,
    run_cv_interview_pipeline,
    run_cv_practice_evaluation,
    to_export_dict,
    to_practice_export_dict,
)
from interview_app.services.interview_generator import generate_questions_from_settings
from interview_app.storage.sessions import save_session
from interview_app.ui.display import (
    show_cv_analysis_bundle,
    show_cv_practice_bundle,
    show_cv_practice_evaluation_batch,
    show_error,
    show_evaluation_result,
    show_guardrail_summary,
    show_llm_response,
    show_prompt_debug,
    show_settings_debug,
)
from interview_app.ui.strategy_comparison import (
    render_comparison_results,
    render_evaluation_section,
)
from interview_app.ui.theme import render_configuration_pill_bar
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


def _render_section_heading(title: str, subtitle: str) -> None:
    """Primary section title + muted subtext (workspace panels)."""
    safe_t = html.escape(title)
    safe_s = html.escape(subtitle)
    st.markdown(
        f'<div class="ia-section-head"><h2 class="ia-section-title">{safe_t}</h2>'
        f'<p class="ia-section-sub">{safe_s}</p></div>',
        unsafe_allow_html=True,
    )


def render_workspace_navigation(tab_labels: list[str]) -> None:
    """
    Primary workspace navigation (segmented control).

    Uses `ia_workspace_tab` session state so sidebar shortcuts stay in sync.
    (Streamlit `st.tabs` cannot be driven from session state; segmented buttons do.)
    """
    st.markdown('<div class="ia-workspace-nav-label">Workspace</div>', unsafe_allow_html=True)
    with st.container(border=True):
        cols = st.columns(len(tab_labels), gap="small")
        for i, label in enumerate(tab_labels):
            with cols[i]:
                active = st.session_state.ia_workspace_tab == label
                if st.button(
                    label,
                    key=f"ia_ws_nav_{i}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                ):
                    st.session_state.ia_workspace_tab = label
                    st.rerun()
    st.divider()


def render_main_content(settings: UISettings) -> None:
    """Workspace: summary bar + primary navigation + tab panels."""
    init_session_state()

    render_configuration_summary_bar(settings)

    tab_labels = list(WORKSPACE_TAB_LABELS)
    if "ia_workspace_tab" not in st.session_state:
        st.session_state.ia_workspace_tab = tab_labels[0]
    if st.session_state.ia_workspace_tab not in tab_labels:
        st.session_state.ia_workspace_tab = tab_labels[0]

    render_workspace_navigation(tab_labels)

    tab = st.session_state.ia_workspace_tab

    if tab == tab_labels[0]:
        _render_mock_interview_tab(settings)
    elif tab == tab_labels[1]:
        _render_question_generation_tab(settings)
    elif tab == tab_labels[2]:
        _render_cv_interview_tab(settings)
    else:
        _render_answer_feedback_tab(settings)


def _session_openai_key() -> str | None:
    """Explicit BYO key for this Streamlit session, or None for Demo (server env key)."""
    return openai_api_key_for_llm(dict(st.session_state))


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
                    session_state=dict(st.session_state),
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
    _render_section_heading(
        "Mock Interview",
        "Answer as you would live. The coach uses your sidebar configuration and adapts each turn.",
    )

    with st.expander("How to use", expanded=False):
        st.markdown(
            "Type a greeting or **Let's start** for your first question. "
            "After each answer you get brief feedback and a follow-up. "
            "Adjust role and round in the sidebar anytime."
        )

    _render_session_row_compact(settings)

    messages = get_messages()
    with st.container(border=True):
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
                    settings,
                    updated,
                    session_state=dict(st.session_state),
                    openai_api_key=_session_openai_key(),
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
            gen_result = generate_questions_from_settings(
                settings=settings,
                prompt_strategy=settings.prompt_strategy,
                n_questions=n_questions,
                session_state=dict(st.session_state),
                response_language=resolved_lang,
                openai_api_key=_session_openai_key(),
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
    _render_section_heading(
        "Interview Questions",
        "Generate a focused set of prompts from your current sidebar configuration.",
    )
    st.caption(
        f"**Active prompt strategy:** {label_for_prompt_strategy(settings.prompt_strategy)}"
    )

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

    _strategy_labels = [lbl for lbl, _ in PROMPT_STRATEGY_OPTIONS]
    with st.container(border=True):
        st.markdown("### Strategy Comparison")
        st.caption("Select strategies to compare")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.selectbox(
                "Strategy A",
                options=_strategy_labels,
                index=0,
                key="ia_compare_sel_a",
            )
        with sc2:
            st.selectbox(
                "Strategy B",
                options=_strategy_labels,
                index=min(1, len(_strategy_labels) - 1),
                key="ia_compare_sel_b",
            )

        if st.button(
            "Compare Selected Strategies",
            use_container_width=True,
            key="btn_compare_selected_strategies",
            help="Compares two strategies using your current sidebar setup and number of questions.",
        ):
            ok_title, _ = validate_role_title(settings.role_title)
            if not ok_title:
                st.warning("Set a **role title** in the sidebar.")
            else:
                la = str(st.session_state.get("ia_compare_sel_a", _strategy_labels[0]))
                lb = str(st.session_state.get("ia_compare_sel_b", _strategy_labels[1]))
                ka = prompt_strategy_key_from_label(la)
                kb = prompt_strategy_key_from_label(lb)
                if ka == kb:
                    st.warning("Choose two **different** strategies to compare.")
                else:
                    jd = settings.job_description or ""
                    if st.session_state.get("response_language") is None and jd.strip():
                        st.session_state.response_language = detect_language(jd)
                    resolved_lang = st.session_state.get("response_language") or DEFAULT_LANGUAGE
                    nq = int(st.session_state.get("ia_n_questions", 5))
                    err_a = ""
                    err_b = ""
                    with st.spinner("Comparing strategies…"):
                        try:
                            gen_a = generate_questions_from_settings(
                                settings=settings,
                                prompt_strategy=ka,
                                n_questions=nq,
                                session_state=dict(st.session_state),
                                skip_session_rate_limit=False,
                                response_language=resolved_lang,
                                openai_api_key=_session_openai_key(),
                            )
                        except Exception as exc:
                            gen_a = None
                            err_a = safe_user_message(exc)
                        else:
                            err_a = ""
                        try:
                            gen_b = generate_questions_from_settings(
                                settings=settings,
                                prompt_strategy=kb,
                                n_questions=nq,
                                session_state=dict(st.session_state),
                                skip_session_rate_limit=True,
                                response_language=resolved_lang,
                                openai_api_key=_session_openai_key(),
                            )
                        except Exception as exc:
                            gen_b = None
                            err_b = safe_user_message(exc)
                        else:
                            err_b = ""

                        text_a = ""
                        text_b = ""
                        ok_a = False
                        ok_b = False
                        if gen_a is not None:
                            ok_a = bool(
                                gen_a.ok
                                and gen_a.response
                                and (gen_a.response.text or "").strip()
                            )
                            if gen_a.ok and gen_a.response:
                                text_a = (gen_a.response.text or "").strip()
                            elif not gen_a.ok:
                                err_a = gen_a.error or err_a or "Generation failed."
                        if gen_b is not None:
                            ok_b = bool(
                                gen_b.ok
                                and gen_b.response
                                and (gen_b.response.text or "").strip()
                            )
                            if gen_b.ok and gen_b.response:
                                text_b = (gen_b.response.text or "").strip()
                            elif not gen_b.ok:
                                err_b = gen_b.error or err_b or "Generation failed."

                        st.session_state.ia_compare_pair = {
                            "a_key": ka,
                            "b_key": kb,
                            "label_a": la,
                            "label_b": lb,
                            "text_a": text_a,
                            "text_b": text_b,
                            "ok_a": ok_a,
                            "ok_b": ok_b,
                            "err_a": err_a,
                            "err_b": err_b,
                        }

    pair = st.session_state.get("ia_compare_pair")
    if isinstance(pair, dict) and pair:
        with st.container(border=True):
            render_comparison_results(
                label_a=str(pair["label_a"]),
                label_b=str(pair["label_b"]),
                key_a=str(pair["a_key"]),
                key_b=str(pair["b_key"]),
                text_a=str(pair.get("text_a", "")),
                text_b=str(pair.get("text_b", "")),
                ok_a=bool(pair.get("ok_a")),
                ok_b=bool(pair.get("ok_b")),
                err_a=str(pair.get("err_a", "")),
                err_b=str(pair.get("err_b", "")),
            )
        with st.container(border=True):
            render_evaluation_section(
                settings=settings,
                key_a=str(pair["a_key"]),
                key_b=str(pair["b_key"]),
                label_a=str(pair["label_a"]),
                label_b=str(pair["label_b"]),
            )

    if settings.show_debug:
        nq = int(st.session_state.get("ia_n_questions", 5))
        show_settings_debug(
            settings=settings,
            extra={
                "n_questions": nq,
                "job_description_len": len(settings.job_description or ""),
            },
        )


def _render_cv_interview_tab(settings: UISettings) -> None:
    """Upload CV, run extraction + interview generation with guardrails (practice vs full prep)."""
    _render_section_heading(
        "CV Interview Prep",
        "Upload your resume (PDF or DOCX). Text is extracted and cleaned, summarized into structured "
        "fields, then used for interview prep grounded in your CV.",
    )

    uploader_key = f"cv_file_uploader_v{cvs.get_cv_workspace_version(st.session_state)}"
    uploaded = st.file_uploader(
        "CV file",
        type=["pdf", "docx"],
        help="PDF and Word (.docx) supported. Size limit is enforced server-side (default 5 MB).",
        key=uploader_key,
    )
    has_uploaded_file = uploaded is not None

    target_role = st.text_input(
        "Target role",
        value=settings.role_title or "",
        help="Questions are tailored to this title and your CV.",
        key="cv_target_role_input",
    )

    interview_type = st.selectbox(
        "Interview type",
        options=["HR / behavioral", "technical", "mixed"],
        index=2,
        key="cv_interview_type",
    )

    difficulty = st.selectbox(
        "Difficulty",
        options=["easy", "medium", "hard"],
        index=1,
        key="cv_difficulty",
    )

    n_questions = int(
        st.number_input(
            "Number of questions",
            min_value=1,
            max_value=20,
            value=int(st.session_state.get("cv_n_questions", 5)),
            key="cv_n_questions",
        )
    )

    with st.expander("Optional: company & job context", expanded=False):
        target_company = st.text_input(
            "Target company (optional)",
            value="",
            key="cv_target_company",
        )
        extra_job = st.text_area(
            "Job description or extra context (optional)",
            value="",
            height=90,
            key="cv_extra_job_context",
        )

    analysis_ready = cvs.analysis_ready(st.session_state)
    cv_ver = cvs.get_cv_workspace_version(st.session_state)

    st.markdown("**What do you want to run?**")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.caption("Practice: write your own answers, then get feedback.")
        btn_practice = st.button(
            "Analyze CV & generate questions",
            type="primary",
            use_container_width=True,
            key="cv_btn_practice",
            disabled=not has_uploaded_file,
        )
    with col_b:
        st.caption("Ready-made: overview, model answers, and follow-ups.")
        btn_full = st.button(
            "Analyze CV & generate full prep",
            use_container_width=True,
            key="cv_btn_full_prep",
            disabled=not has_uploaded_file,
        )
    with col_c:
        st.caption("Clear everything and start over.")
        reset_cv = st.button(
            "Reset session",
            use_container_width=True,
            key="cv_btn_reset",
            help="Clear CV results, practice answers, evaluations, errors, and file selection.",
        )

    if not has_uploaded_file:
        st.info("Upload a PDF or DOCX to enable **Analyze** actions.")

    if reset_cv:
        cvs.clear_cv_workspace(st.session_state)
        st.rerun()

    def _apply_cv_result(
        result: CVInterviewServiceResult,
        *,
        step: str,
        file_meta: dict[str, Any] | None = None,
    ) -> None:
        show_guardrail_summary(guardrails=result.guardrails)
        if not result.ok:
            st.session_state[cvs.KEY_LAST_ERROR] = result.error or "Unknown error."
            if step == "analyze":
                cvs.on_full_analyze_failure(st.session_state)
            elif result.generation_mode == "practice_questions":
                cvs.on_practice_regenerate_failure(st.session_state)
            else:
                cvs.on_regenerate_failure(st.session_state)
            return

        if result.practice_bundle is not None:
            if result.bundle is not None:
                st.session_state[cvs.KEY_LAST_ERROR] = "Internal error: both practice and full prep bundles set."
                cvs.on_full_analyze_failure(st.session_state)
                return
            st.session_state.pop(cvs.KEY_LAST_ERROR, None)
            st.session_state[cvs.KEY_STRUCTURED] = result.practice_bundle.structured_extraction.model_dump()
            st.session_state[cvs.KEY_PRACTICE_BUNDLE] = result.practice_bundle.model_dump()
            st.session_state[cvs.KEY_ACTIVE_MODE] = "practice"
            st.session_state.pop(cvs.KEY_BUNDLE, None)
            st.session_state.pop(cvs.KEY_EXPORT, None)
            st.session_state.pop(cvs.KEY_PRACTICE_EVAL_BATCH, None)
            st.session_state.pop(cvs.KEY_PRACTICE_EVAL_ERROR, None)
            st.session_state[cvs.KEY_DEBUG_RAW_LEN] = len(result.raw_extracted_text or "")
            st.session_state[cvs.KEY_DEBUG_CLEAN] = (result.cleaned_text_for_llm or "")[:2000]
            if result.file_hash:
                st.session_state[cvs.KEY_FILE_HASH] = result.file_hash
            if step == "analyze" and file_meta:
                st.session_state[cvs.KEY_FILE_META] = file_meta
            if step == "analyze":
                cvs.on_full_analyze_success(st.session_state)
            else:
                cvs.on_regenerate_success(st.session_state)
            if result.regenerate_only:
                st.toast("Practice questions regenerated (same CV analysis).")
            else:
                st.toast("CV analyzed — practice questions ready.")
        elif result.bundle is not None:
            st.session_state.pop(cvs.KEY_LAST_ERROR, None)
            st.session_state[cvs.KEY_STRUCTURED] = result.bundle.structured_extraction.model_dump()
            st.session_state[cvs.KEY_BUNDLE] = result.bundle.model_dump()
            st.session_state[cvs.KEY_EXPORT] = to_export_dict(result.bundle)
            st.session_state[cvs.KEY_ACTIVE_MODE] = "full_prep"
            st.session_state.pop(cvs.KEY_PRACTICE_BUNDLE, None)
            st.session_state.pop(cvs.KEY_PRACTICE_EVAL_BATCH, None)
            st.session_state.pop(cvs.KEY_PRACTICE_EVAL_ERROR, None)
            st.session_state[cvs.KEY_DEBUG_RAW_LEN] = len(result.raw_extracted_text or "")
            st.session_state[cvs.KEY_DEBUG_CLEAN] = (result.cleaned_text_for_llm or "")[:2000]
            if result.file_hash:
                st.session_state[cvs.KEY_FILE_HASH] = result.file_hash
            if step == "analyze" and file_meta:
                st.session_state[cvs.KEY_FILE_META] = file_meta
            if step == "analyze":
                cvs.on_full_analyze_success(st.session_state)
            else:
                cvs.on_regenerate_success(st.session_state)
            if result.regenerate_only:
                st.toast("Full prep regenerated (same CV analysis).")
            else:
                st.toast("CV analyzed — full prep ready.")
        else:
            st.session_state[cvs.KEY_LAST_ERROR] = "No generation output returned."
            if step == "analyze":
                cvs.on_full_analyze_failure(st.session_state)
            elif result.generation_mode == "practice_questions":
                cvs.on_practice_regenerate_failure(st.session_state)
            else:
                cvs.on_regenerate_failure(st.session_state)
            return

        if settings.show_debug:
            meta = [
                {
                    "model": r.model,
                    "usage": r.usage.model_dump() if r.usage else None,
                    "raw_response_id": r.raw_response_id,
                    "phase": "regenerate_only" if result.regenerate_only else "full",
                    "generation_mode": result.generation_mode,
                }
                for r in result.llm_responses
            ]
            with st.expander("LLM calls (debug)", expanded=False):
                st.code(json.dumps(meta, indent=2), language="json")
            if result.extraction_system_prompt and result.extraction_user_prompt:
                with st.expander("Prompts: CV extraction (debug)", expanded=False):
                    show_prompt_debug(
                        system_prompt=result.extraction_system_prompt,
                        user_prompt=result.extraction_user_prompt,
                    )
            if result.generation_system_prompt and result.generation_user_prompt:
                with st.expander("Prompts: interview generation (debug)", expanded=False):
                    show_prompt_debug(
                        system_prompt=result.generation_system_prompt,
                        user_prompt=result.generation_user_prompt,
                    )
            with st.expander("Extracted text preview (debug)", expanded=False):
                st.caption("First ~2000 chars after cleaning / guardrails (not the raw file).")
                st.code(
                    st.session_state.get(cvs.KEY_DEBUG_CLEAN) or "",
                    language="text",
                )
            fm = st.session_state.get(cvs.KEY_FILE_META) or {}
            show_settings_debug(
                settings=settings,
                extra={
                    "cv_file_hash": result.file_hash,
                    "cv_raw_extracted_chars": st.session_state.get(cvs.KEY_DEBUG_RAW_LEN),
                    "cv_file_meta": fm,
                    "cv_analysis_ready": cvs.analysis_ready(st.session_state),
                    "cv_active_mode": st.session_state.get(cvs.KEY_ACTIVE_MODE),
                },
            )

    if btn_practice:
        st.session_state.pop(cvs.KEY_LAST_ERROR, None)
        if not uploaded:
            st.warning("Please upload a PDF or DOCX file.")
        else:
            try:
                file_bytes = uploaded.getvalue()
                with st.spinner("Analyzing CV and generating practice questions…"):
                    result = run_cv_interview_pipeline(
                        filename=uploaded.name,
                        file_bytes=file_bytes,
                        target_role=target_role,
                        interview_type=interview_type,
                        difficulty=difficulty,
                        n_questions=n_questions,
                        model=settings.model_preset,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                        top_p=settings.top_p,
                        session_state=dict(st.session_state),
                        regenerate_questions_only=False,
                        target_company=target_company,
                        extra_job_context=extra_job,
                        generation_mode="practice_questions",
                        openai_api_key=_session_openai_key(),
                    )
            except Exception as exc:
                st.session_state[cvs.KEY_LAST_ERROR] = safe_user_message(exc)
                cvs.on_full_analyze_failure(st.session_state)
            else:
                _apply_cv_result(
                    result,
                    step="analyze",
                    file_meta={
                        "filename": uploaded.name,
                        "size_bytes": len(file_bytes),
                    },
                )

    elif btn_full:
        st.session_state.pop(cvs.KEY_LAST_ERROR, None)
        if not uploaded:
            st.warning("Please upload a PDF or DOCX file.")
        else:
            try:
                file_bytes = uploaded.getvalue()
                with st.spinner("Analyzing CV and generating full prep (overview + answers + follow-ups)…"):
                    result = run_cv_interview_pipeline(
                        filename=uploaded.name,
                        file_bytes=file_bytes,
                        target_role=target_role,
                        interview_type=interview_type,
                        difficulty=difficulty,
                        n_questions=n_questions,
                        model=settings.model_preset,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                        top_p=settings.top_p,
                        session_state=dict(st.session_state),
                        regenerate_questions_only=False,
                        target_company=target_company,
                        extra_job_context=extra_job,
                        generation_mode="full_prep",
                        openai_api_key=_session_openai_key(),
                    )
            except Exception as exc:
                st.session_state[cvs.KEY_LAST_ERROR] = safe_user_message(exc)
                cvs.on_full_analyze_failure(st.session_state)
            else:
                _apply_cv_result(
                    result,
                    step="analyze",
                    file_meta={
                        "filename": uploaded.name,
                        "size_bytes": len(file_bytes),
                    },
                )

    st.markdown("---")
    st.markdown("**Optional: regenerate without re-uploading** (uses the last successful CV analysis).")
    regen_col1, regen_col2 = st.columns(2)
    with regen_col1:
        regen_practice = st.button(
            "Regenerate practice questions",
            use_container_width=True,
            key="cv_btn_regen_practice",
            disabled=not analysis_ready,
            help="Same CV as your last successful analyze; only regenerates practice questions.",
        )
    with regen_col2:
        regen_full = st.button(
            "Regenerate full prep",
            use_container_width=True,
            key="cv_btn_regen_full",
            disabled=not analysis_ready,
            help="Same CV as your last successful analyze; only regenerates full prep content.",
        )

    if regen_practice:
        st.session_state.pop(cvs.KEY_LAST_ERROR, None)
        raw = st.session_state.get(cvs.KEY_STRUCTURED)
        if not raw:
            st.warning("Run **Analyze CV** successfully first.")
        else:
            try:
                cached_extraction = CVStructuredExtraction.model_validate(raw)
                with st.spinner("Regenerating practice questions…"):
                    result = run_cv_interview_pipeline(
                        filename=None,
                        file_bytes=None,
                        target_role=target_role,
                        interview_type=interview_type,
                        difficulty=difficulty,
                        n_questions=n_questions,
                        model=settings.model_preset,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                        top_p=settings.top_p,
                        session_state=dict(st.session_state),
                        regenerate_questions_only=True,
                        cached_extraction=cached_extraction,
                        cached_file_hash=str(st.session_state.get(cvs.KEY_FILE_HASH) or ""),
                        target_company=target_company,
                        extra_job_context=extra_job,
                        generation_mode="practice_questions",
                        openai_api_key=_session_openai_key(),
                    )
            except Exception as exc:
                st.session_state[cvs.KEY_LAST_ERROR] = safe_user_message(exc)
                cvs.on_practice_regenerate_failure(st.session_state)
            else:
                _apply_cv_result(result, step="regenerate")

    elif regen_full:
        st.session_state.pop(cvs.KEY_LAST_ERROR, None)
        raw = st.session_state.get(cvs.KEY_STRUCTURED)
        if not raw:
            st.warning("Run **Analyze CV** successfully first.")
        else:
            try:
                cached_extraction = CVStructuredExtraction.model_validate(raw)
                with st.spinner("Regenerating full prep…"):
                    result = run_cv_interview_pipeline(
                        filename=None,
                        file_bytes=None,
                        target_role=target_role,
                        interview_type=interview_type,
                        difficulty=difficulty,
                        n_questions=n_questions,
                        model=settings.model_preset,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                        top_p=settings.top_p,
                        session_state=dict(st.session_state),
                        regenerate_questions_only=True,
                        cached_extraction=cached_extraction,
                        cached_file_hash=str(st.session_state.get(cvs.KEY_FILE_HASH) or ""),
                        target_company=target_company,
                        extra_job_context=extra_job,
                        generation_mode="full_prep",
                        openai_api_key=_session_openai_key(),
                    )
            except Exception as exc:
                st.session_state[cvs.KEY_LAST_ERROR] = safe_user_message(exc)
                cvs.on_regenerate_failure(st.session_state)
            else:
                _apply_cv_result(result, step="regenerate")

    err_banner = st.session_state.get(cvs.KEY_LAST_ERROR)
    if err_banner:
        st.error(f"**CV step failed**\n\n{err_banner}")

    active_mode = str(st.session_state.get(cvs.KEY_ACTIVE_MODE) or "none")
    practice_raw = st.session_state.get(cvs.KEY_PRACTICE_BUNDLE)
    bundle_raw = st.session_state.get(cvs.KEY_BUNDLE)
    show_practice = active_mode == "practice" and bool(practice_raw)
    show_full = active_mode == "full_prep" and bool(bundle_raw)

    if show_practice:
        try:
            pb = CVPracticeBundle.model_validate(practice_raw)
            show_cv_practice_bundle(bundle=pb)
            st.markdown("### Your practice questions")
            st.caption("Answer each prompt, then run evaluation when ready.")
            any_answer = False
            for i, item in enumerate(pb.practice_generation.interview_questions):
                st.markdown(
                    f"**{i + 1}. ({item.category} · {item.difficulty})** {item.question}"
                )
                if item.why_this_question:
                    st.caption(f"Why this question: {item.why_this_question}")
                ans = st.text_area(
                    "Your answer",
                    height=120,
                    key=f"cv_pa_{cv_ver}_{i}",
                    label_visibility="collapsed",
                    placeholder="Type your answer here…",
                )
                if (ans or "").strip():
                    any_answer = True

            st.session_state[cvs.KEY_PRACTICE_ANSWERS] = {
                str(i): (st.session_state.get(f"cv_pa_{cv_ver}_{i}") or "")
                for i in range(len(pb.practice_generation.interview_questions))
            }

            eval_err = st.session_state.get(cvs.KEY_PRACTICE_EVAL_ERROR)
            if eval_err:
                st.error(f"**Evaluation failed**\n\n{eval_err}")

            if st.button(
                "Evaluate my answers",
                type="primary",
                use_container_width=True,
                key="cv_btn_evaluate_practice",
                disabled=not any_answer,
            ):
                raw_struct = st.session_state.get(cvs.KEY_STRUCTURED)
                if not raw_struct or not practice_raw:
                    st.warning("Practice session is incomplete. Run **Analyze CV & generate questions** again.")
                else:
                    qa_pairs: list[tuple[str, str]] = []
                    for i, q in enumerate(pb.practice_generation.interview_questions):
                        a = (st.session_state.get(f"cv_pa_{cv_ver}_{i}") or "").strip()
                        if a:
                            qa_pairs.append((q.question, a))
                    try:
                        extraction = CVStructuredExtraction.model_validate(raw_struct)
                        with st.spinner("Evaluating your answers…"):
                            eval_result = run_cv_practice_evaluation(
                                structured_extraction=extraction,
                                qa_pairs=qa_pairs,
                                target_role=target_role,
                                interview_type=interview_type,
                                difficulty=difficulty,
                                model=settings.model_preset,
                                temperature=settings.temperature,
                                max_tokens=settings.max_tokens,
                                top_p=settings.top_p,
                                session_state=dict(st.session_state),
                                openai_api_key=_session_openai_key(),
                            )
                    except Exception as exc:
                        st.session_state[cvs.KEY_PRACTICE_EVAL_ERROR] = safe_user_message(exc)
                    else:
                        show_guardrail_summary(guardrails=eval_result.guardrails)
                        if not eval_result.ok or eval_result.batch is None:
                            st.session_state[cvs.KEY_PRACTICE_EVAL_ERROR] = (
                                eval_result.error or "Evaluation failed."
                            )
                        else:
                            st.session_state.pop(cvs.KEY_PRACTICE_EVAL_ERROR, None)
                            st.session_state[cvs.KEY_PRACTICE_EVAL_BATCH] = (
                                eval_result.batch.model_dump()
                            )
                            st.toast("Evaluation complete.")
                            if settings.show_debug and eval_result.system_prompt and eval_result.user_prompt:
                                show_prompt_debug(
                                    system_prompt=eval_result.system_prompt,
                                    user_prompt=eval_result.user_prompt,
                                )
                        st.rerun()

            eval_raw = st.session_state.get(cvs.KEY_PRACTICE_EVAL_BATCH)
            if eval_raw:
                try:
                    eval_batch = CVPracticeEvaluationBatch.model_validate(eval_raw)
                    show_cv_practice_evaluation_batch(batch=eval_batch)
                except Exception:
                    pass

            export_p = to_practice_export_dict(pb)
            st.download_button(
                label="Export practice questions (JSON)",
                data=json.dumps(export_p, indent=2, ensure_ascii=False),
                file_name="cv_practice_questions.json",
                mime="application/json",
                key="cv_download_practice_export",
            )
        except Exception:
            pass

    if show_full:
        try:
            bundle = CVAnalysisBundle.model_validate(bundle_raw)
            show_cv_analysis_bundle(bundle=bundle)
            export_payload = st.session_state.get(cvs.KEY_EXPORT)
            if isinstance(export_payload, dict):
                st.download_button(
                    label="Export questions & answers (JSON)",
                    data=json.dumps(export_payload, indent=2, ensure_ascii=False),
                    file_name="cv_interview_prep.json",
                    mime="application/json",
                    key="cv_download_export_area",
                )
        except Exception:
            pass

    if settings.show_debug and not btn_practice and not btn_full and not regen_practice and not regen_full:
        show_settings_debug(
            settings=settings,
            extra={
                "cv_analysis_ready": cvs.analysis_ready(st.session_state),
                "cv_workspace_version": cvs.get_cv_workspace_version(st.session_state),
                "cv_active_mode": active_mode,
            },
        )


def _render_answer_feedback_tab(settings: UISettings) -> None:
    """Paste question + answer; show structured evaluation."""
    _render_section_heading(
        "Feedback / Evaluation",
        "Evaluate a single answer against your configured role and interview context.",
    )

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
                        openai_api_key=_session_openai_key(),
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
