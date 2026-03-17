from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from interview_app.llm import MODEL_PRESETS
from interview_app.prompts.prompt_templates import load_template


@dataclass(frozen=True)
class UISettings:
    interview_type: str
    role_title: str
    seniority: str
    prompt_strategy: str
    model_preset: str
    temperature: float
    max_tokens: int
    show_debug: bool


def render_sidebar_controls() -> UISettings:
    st.sidebar.header("Settings")

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

    return UISettings(
        interview_type=interview_type,
        role_title=role_title,
        seniority=seniority,
        prompt_strategy=prompt_strategy,
        model_preset=model_preset,
        temperature=temperature,
        max_tokens=max_tokens,
        show_debug=show_debug,
    )

