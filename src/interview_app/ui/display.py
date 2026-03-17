from __future__ import annotations

import json
from typing import Any

import streamlit as st

from interview_app.app.controls import UISettings
from interview_app.security.guards import GuardrailResult
from interview_app.utils.types import LLMResponse


def show_placeholder_result(*, title: str, body: str) -> None:
    st.success(title)
    st.markdown(body)


def show_error(*, title: str, body: str) -> None:
    st.error(title)
    st.markdown(body)


def show_llm_response(*, title: str, response: LLMResponse) -> None:
    st.success(title)
    if response.text:
        st.markdown(response.text)
    else:
        st.warning("No text returned by the model.")

    with st.expander("Response metadata", expanded=False):
        st.code(
            json.dumps(
                {
                    "model": response.model,
                    "usage": (response.usage.model_dump() if response.usage else None),
                    "raw_response_id": response.raw_response_id,
                },
                indent=2,
            ),
            language="json",
        )


def show_guardrail_summary(*, guardrails: dict[str, GuardrailResult]) -> None:
    if not guardrails:
        return

    flagged = {k: v for k, v in guardrails.items() if not v.ok or v.flags}
    if not flagged:
        return

    with st.expander("Guardrails", expanded=False):
        for name, res in flagged.items():
            st.markdown(f"**{name}**")
            st.code(res.model_dump_json(indent=2), language="json")


def show_prompt_debug(*, system_prompt: str, user_prompt: str) -> None:
    with st.expander("Prompts (debug)", expanded=False):
        st.markdown("**System**")
        st.code(system_prompt, language="markdown")
        st.markdown("**User**")
        st.code(user_prompt, language="markdown")


def show_settings_debug(*, settings: UISettings, extra: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "interview_type": settings.interview_type,
        "role_title": settings.role_title,
        "seniority": settings.seniority,
        "prompt_strategy": settings.prompt_strategy,
        "model_preset": settings.model_preset,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
    }
    if extra:
        payload["extra"] = extra

    with st.expander("Debug", expanded=False):
        st.code(json.dumps(payload, indent=2), language="json")

