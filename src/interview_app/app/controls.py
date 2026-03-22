"""Streamlit sidebar: appearance, role and interview setup, advanced options, actions, saved sessions.

`render_sidebar_configuration` returns a frozen `UISettings` snapshot for services and layout.
"""

from __future__ import annotations

import streamlit as st

from interview_app.app.interview_form_config import (
    DIFFICULTY_MODES,
    INTERVIEW_ROUNDS,
    ROLE_CATEGORIES,
    SENIORITY_OPTIONS,
    TECHNICAL_CATEGORIES,
    build_focus_options,
    default_focus_for_round,
    default_persona_for_round,
    infer_difficulty_from_context,
    role_title_placeholder,
    validate_role_title,
)
from interview_app.llm import MODEL_PRESETS
from interview_app.prompts.personas import PERSONA_KEYS
from interview_app.prompts.prompt_templates import load_template
from interview_app.storage.sessions import list_sessions, load_session
from interview_app.app.conversation_state import (
    clear_messages,
    load_session_into_state,
)
from interview_app.utils.language import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    get_language_name,
    langdetect_available,
)
from interview_app.app.ui_settings import UISettings, WORKSPACE_TAB_LABELS


def _sidebar_section_title(title: str, hint: str | None = None) -> None:
    st.sidebar.markdown(f"**{title}**")
    if hint:
        st.sidebar.caption(hint)


def render_sidebar_configuration() -> UISettings:
    """
    Render the full configuration sidebar and return a frozen `UISettings` snapshot.

    Sections: Appearance, Role, Interview setup, Advanced (expander), workflow actions,
    saved sessions.
    """
    sb = st.sidebar

    # ── A. Appearance ──
    _sidebar_section_title("Appearance", "Theme for the workspace.")
    dark = sb.toggle(
        "Dark mode",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode_toggle",
        help="Switch between light and dark theme.",
    )
    if dark != st.session_state.get("dark_mode", False):
        st.session_state.dark_mode = dark
        st.rerun()

    sb.divider()

    # ── B. Role information ──
    _sidebar_section_title(
        "Role information",
        "Target role shapes difficulty, tone, and scenarios.",
    )
    role_category = sb.selectbox(
        "Category",
        options=list(ROLE_CATEGORIES),
        index=0,
        help="Job family for tailored scenarios.",
    )
    seniority = sb.selectbox(
        "Seniority",
        options=list(SENIORITY_OPTIONS),
        index=2,
        help="Level you are targeting.",
    )
    placeholder = role_title_placeholder(role_category)
    role_title_raw = sb.text_input(
        "Role title",
        value="",
        placeholder=placeholder,
        help="Exact title as listed on the job posting or target role.",
    )
    job_description = sb.text_area(
        "Job description",
        value="",
        height=100,
        placeholder="Paste the job description or key requirements (recommended).",
        help="Optional; strongly recommended for realistic prompts.",
    )

    sb.divider()

    # ── C. Interview setup ──
    _sidebar_section_title(
        "Interview setup",
        "Stage, emphasis, interviewer style, and output language.",
    )

    focus_options = build_focus_options(role_category, seniority)
    if st.session_state.get("interview_focus_sel") not in focus_options:
        st.session_state.interview_focus_sel = focus_options[0]

    interview_round = sb.selectbox(
        "Interview round",
        options=list(INTERVIEW_ROUNDS),
        index=0,
        help="Hiring stage to simulate.",
        key="ia_interview_round_select",
    )
    if st.session_state.get("_ia_round_tracker") != interview_round:
        st.session_state._ia_round_tracker = interview_round
        focus_opts = build_focus_options(role_category, seniority)
        d = default_focus_for_round(interview_round)
        st.session_state.interview_focus_sel = d if d in focus_opts else focus_opts[0]
        st.session_state.persona_sel = default_persona_for_round(
            interview_round, persona_keys=PERSONA_KEYS
        )

    focus_options = build_focus_options(role_category, seniority)
    if st.session_state.get("interview_focus_sel") not in focus_options:
        st.session_state.interview_focus_sel = focus_options[0]

    sb.selectbox(
        "Interview focus",
        options=focus_options,
        key="interview_focus_sel",
        help="Skills and format to emphasize.",
    )
    sb.selectbox(
        "Interviewer persona",
        options=list(PERSONA_KEYS),
        key="persona_sel",
        help="Who is asking and how they evaluate.",
    )

    lang_options = ["Auto (detect)"] + [
        f"{name} ({code})" for code, name in SUPPORTED_LANGUAGES.items()
    ]
    current = st.session_state.get("response_language")
    if current:
        try:
            lidx = list(SUPPORTED_LANGUAGES.keys()).index(current) + 1
        except ValueError:
            lidx = 0
    else:
        lidx = 0
    lang_choice = sb.selectbox(
        "Response language",
        options=lang_options,
        index=lidx,
        help="Output language for model responses.",
        key="ia_response_lang_select",
    )
    if lang_choice == "Auto (detect)":
        st.session_state.response_language = None
    else:
        code = lang_choice.split("(")[-1].rstrip(")")
        st.session_state.response_language = (
            code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        )
    if current:
        sb.caption(f"Active: {get_language_name(current)}")
    if lang_choice == "Auto (detect)" and not langdetect_available():
        sb.warning(
            "Install `langdetect` for automatic language detection (`pip install langdetect`)."
        )

    if role_category in TECHNICAL_CATEGORIES:
        sb.caption("Technical and architecture-style content is emphasized.")

    interview_focus = str(st.session_state.get("interview_focus_sel", focus_options[0]))
    persona = str(st.session_state.get("persona_sel", PERSONA_KEYS[1]))

    sb.divider()

    # ── D. Advanced ──
    with sb.expander("Advanced settings", expanded=False):
        sb.caption("Difficulty, model, and sampling parameters.")
        question_difficulty_mode = sb.selectbox(
            "Difficulty mode",
            options=list(DIFFICULTY_MODES),
            index=0,
            help="Auto uses seniority and round; choose Easy–Expert to override.",
        )

        effective_difficulty = infer_difficulty_from_context(
            seniority=seniority,
            interview_round=interview_round,
            manual_mode=question_difficulty_mode,
        )
        if question_difficulty_mode == "Auto":
            sb.info(
                f"Calibrated difficulty: **{effective_difficulty}** (from seniority and round)."
            )
        else:
            sb.caption(f"Override: **{question_difficulty_mode}**")

        sb.markdown("**Model & generation**")
        prompt_strategy = sb.selectbox(
            "Prompt strategy",
            options=[
                "zero_shot",
                "few_shot",
                "chain_of_thought",
                "structured_output",
                "role_based",
            ],
            index=0,
        )
        try:
            tmpl = load_template(prompt_strategy)
            if tmpl.description:
                sb.caption(tmpl.description)
        except Exception:
            pass

        preset_keys = list(MODEL_PRESETS.keys())
        model_preset = sb.selectbox(
            "Model",
            options=preset_keys,
            index=(
                min(1, len(preset_keys) - 1)
                if "gpt-4o-mini" in preset_keys
                else 0
            ),
        )
        preset = MODEL_PRESETS[model_preset]
        default_top_p = (
            float(preset.default_top_p) if preset.default_top_p is not None else 1.0
        )

        temperature = sb.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=float(preset.default_temperature),
            step=0.05,
        )
        top_p = sb.slider(
            "Top-p",
            min_value=0.0,
            max_value=1.0,
            value=default_top_p,
            step=0.01,
            help="Nucleus sampling; lower values make output more focused.",
        )
        max_tokens = sb.slider(
            "Max tokens",
            min_value=64,
            max_value=4000,
            value=int(preset.default_max_tokens or 800),
            step=64,
        )
        show_debug = sb.toggle(
            "Show debug info",
            value=False,
            help="Expose prompts and settings JSON for troubleshooting.",
        )

    sb.divider()

    # ── E. Workflow shortcuts ──
    _sidebar_section_title("Actions", "Jump to a workspace or reset the transcript.")
    b1, b2 = sb.columns(2)
    with b1:
        if sb.button(
            "Generate questions",
            use_container_width=True,
            key="sb_btn_generate",
            help="Open Interview Questions and run generation.",
        ):
            st.session_state.ia_workspace_tab = WORKSPACE_TAB_LABELS[1]
            st.session_state.ia_pending_generate = True
            st.rerun()
    with b2:
        if sb.button(
            "Mock interview",
            use_container_width=True,
            key="sb_btn_mock",
            help="Open the live chat workspace.",
        ):
            st.session_state.ia_workspace_tab = WORKSPACE_TAB_LABELS[0]
            st.rerun()

    if sb.button(
        "Reset transcript",
        use_container_width=True,
        key="sb_btn_reset",
        help="Clear chat messages; configuration stays as set.",
    ):
        clear_messages()
        st.session_state.current_session_id = None
        st.session_state.session_meta = None
        st.toast("Transcript cleared. Sidebar settings are unchanged.")
        st.rerun()

    sb.divider()

    # ── Saved sessions ──
    _sidebar_section_title("Saved sessions", "Reopen a stored mock interview.")
    _render_sidebar_session_list()

    response_language = st.session_state.get("response_language") or DEFAULT_LANGUAGE
    _, role_title_trimmed = validate_role_title(role_title_raw)

    return UISettings(
        role_category=role_category,
        role_title=role_title_trimmed,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=job_description,
        persona=persona,
        question_difficulty_mode=question_difficulty_mode,
        effective_question_difficulty=effective_difficulty,
        prompt_strategy=prompt_strategy,
        model_preset=model_preset,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        show_debug=show_debug,
        response_language=response_language,
    )


def _format_ts(raw: str) -> str:
    from datetime import datetime

    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%b %d · %H:%M")
    except (ValueError, TypeError):
        return raw[:16].replace("T", " ")


def _render_sidebar_session_list() -> None:
    sb = st.sidebar
    sessions = list_sessions()
    if not sessions:
        sb.caption("No saved sessions yet.")
        return

    for s in sessions[:10]:
        sid = s.get("id", "")
        title = s.get("title", "Untitled")
        created = _format_ts(s.get("created_at", ""))
        col_a, col_b = sb.columns([3, 1])
        with col_a:
            sb.caption(f"**{title}**")
            if created:
                sb.caption(created)
        with col_b:
            if sb.button("Open", key=f"sb_open_{sid}", use_container_width=True):
                loaded = load_session(sid)
                if loaded:
                    meta, messages = loaded
                    load_session_into_state(sid, meta, messages)
                    st.session_state.current_session_id = sid
                    st.session_state.ia_workspace_tab = WORKSPACE_TAB_LABELS[0]
                    st.toast("Session loaded. Open Mock Interview to continue.")
                    st.rerun()
                else:
                    st.sidebar.error("**Load failed**")
                    st.sidebar.caption(f"Could not load session {sid}.")
