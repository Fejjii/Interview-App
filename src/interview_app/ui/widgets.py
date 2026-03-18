from __future__ import annotations

"""
Reusable Streamlit input widgets.

Keeping widgets in a separate module makes `app/layout.py` easier to read and helps
beginners find "where inputs are defined" without digging through service code.
"""

import streamlit as st


def job_description_input() -> str:
    """Multiline input for an optional job description / requirements."""
    return st.text_area(
        "Job description (optional)",
        placeholder="Paste a job description or key requirements…",
        height=180,
    )


def question_context_input() -> str:
    """Multiline input for the interview question being answered."""
    return st.text_area(
        "Question",
        placeholder="Paste the interview question you want to answer…",
        height=140,
    )


def answer_input() -> str:
    """Multiline input for the user's answer."""
    return st.text_area(
        "Your answer",
        placeholder="Write your answer here…",
        height=220,
    )

