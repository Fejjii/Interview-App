from __future__ import annotations

"""
Reusable Streamlit input widgets.

Provides consistent input fields with descriptive labels, help text,
and placeholder guidance for each input type.
"""

import streamlit as st


def job_description_input() -> str:
    """Multiline input for an optional job description / requirements."""
    return st.text_area(
        "Job description",
        placeholder="Paste a job description or key requirements\u2026",
        height=180,
        help="Optional. Providing a job description generates more relevant and targeted questions.",
    )


def question_context_input() -> str:
    """Multiline input for the interview question being answered."""
    return st.text_area(
        "Interview question",
        placeholder="Paste the interview question you want to answer\u2026",
        height=140,
        help="Enter the exact interview question you'd like evaluated.",
        key="ia_feedback_question",
    )


def answer_input() -> str:
    """Multiline input for the user's answer."""
    return st.text_area(
        "Your answer",
        placeholder="Write your answer here\u2026",
        height=220,
        help="Write your best answer. The evaluator will score it and suggest improvements.",
        key="ia_feedback_answer",
    )
