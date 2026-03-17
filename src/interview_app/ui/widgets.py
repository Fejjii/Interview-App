from __future__ import annotations

import streamlit as st


def job_description_input() -> str:
    return st.text_area(
        "Job description (optional)",
        placeholder="Paste a job description or key requirements…",
        height=180,
    )


def question_context_input() -> str:
    return st.text_area(
        "Question",
        placeholder="Paste the interview question you want to answer…",
        height=140,
    )


def answer_input() -> str:
    return st.text_area(
        "Your answer",
        placeholder="Write your answer here…",
        height=220,
    )

