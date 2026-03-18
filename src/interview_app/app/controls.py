from __future__ import annotations

"""
Streamlit sidebar controls and UI settings model.

The goal of this module is to:
- keep Streamlit widget code out of the service layer
- centralize "what knobs exist" (prompt strategy, model preset, temperature, etc.)
- return a single `UISettings` object that other UI code can pass around
"""

from dataclasses import dataclass

import streamlit as st

from interview_app.llm import MODEL_PRESETS
from interview_app.prompts.prompt_templates import load_template
from interview_app.utils.language import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    get_language_name,
    langdetect_available,
)


@dataclass(frozen=True)
class UISettings:
    """All UI-controlled settings that affect prompt building and LLM calls."""

    interview_type: str
    role_title: str
    seniority: str
    prompt_strategy: str
    model_preset: str
    temperature: float
    max_tokens: int
    show_debug: bool
    response_language: str


def render_sidebar_controls() -> UISettings:
    """
    Render sidebar widgets and return a frozen `UISettings` snapshot.

    Streamlit re-runs the script top-to-bottom on every interaction; returning a single
    object keeps downstream code simple and makes the app's "state" explicit.
    """
    st.sidebar.header("Settings")

    # Response language: Auto (detect from input) or fixed choice. Stored in session state.
    lang_options = ["Auto (detect)"] + [f"{name} ({code})" for code, name in SUPPORTED_LANGUAGES.items()]
    current = st.session_state.get("response_language")
    if current:
        try:
            idx = list(SUPPORTED_LANGUAGES.keys()).index(current) + 1
        except ValueError:
            idx = 0
    else:
        idx = 0
    lang_choice = st.sidebar.selectbox(
        "Response language",
        options=lang_options,
        index=idx,
        help="Auto detects from job description or first input; override to fix the output language.",
    )
    if lang_choice == "Auto (detect)":
        st.session_state.response_language = None
    else:
        code = lang_choice.split("(")[-1].rstrip(")")
        st.session_state.response_language = code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    if current:
        st.sidebar.caption(f"Using: {get_language_name(current)}")
    if lang_choice == "Auto (detect)" and not langdetect_available():
        st.sidebar.warning(
            "Auto-detect requires the **langdetect** package. Install with: `pip install langdetect`. "
            "Using English until then, or pick a language above."
        )

    interview_type = st.sidebar.selectbox(
        "Interview type",
        options=["Behavioral", "System design", "Coding", "Leadership"],
        index=0,
    )

    role_title = st.sidebar.text_input("Role title", value="Software Engineer")
    seniority = st.sidebar.selectbox("Seniority", options=["Junior", "Mid", "Senior", "Staff"], index=2)

    prompt_strategy = st.sidebar.selectbox(
        "Prompt strategy",
        options=[
            "zero_shot",
            "few_shot",
            "chain_of_thought",
            "structured_output",
            "role_based",
        ],
        index=0,
        help="Choose one of 5 prompting techniques to compare outputs.",
    )
    try:
        # Pull a short description from the template header to make the UI self-explanatory.
        tmpl = load_template(prompt_strategy)
        if tmpl.description:
            st.sidebar.caption(f"**{prompt_strategy}**: {tmpl.description}")
    except Exception:
        # Best-effort sidebar hint; avoid breaking the app if templates are missing.
        pass

    preset_keys = list(MODEL_PRESETS.keys())
    model_preset = st.sidebar.selectbox(
        "Model preset",
        options=preset_keys,
        index=preset_keys.index("gpt-4o-mini") if "gpt-4o-mini" in preset_keys else 0,
    )
    # Each preset provides reasonable defaults; users can override via sliders below.
    preset = MODEL_PRESETS[model_preset]

    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=float(preset.default_temperature),
        step=0.05,
    )
    max_tokens = st.sidebar.slider(
        "Max tokens",
        min_value=64,
        max_value=4000,
        value=int(preset.default_max_tokens or 800),
        step=64,
    )

    st.sidebar.divider()
    show_debug = st.sidebar.toggle("Show debug", value=False)

    response_language = st.session_state.get("response_language") or DEFAULT_LANGUAGE

    return UISettings(
        interview_type=interview_type,
        role_title=role_title,
        seniority=seniority,
        prompt_strategy=prompt_strategy,
        model_preset=model_preset,
        temperature=temperature,
        max_tokens=max_tokens,
        show_debug=show_debug,
        response_language=response_language,
    )

