from __future__ import annotations

"""
Streamlit page layout and button wiring.

This module renders the main page body (tabs + forms) and is responsible for calling
service-layer functions when the user clicks buttons.

Design note:
- UI code lives here (Streamlit widgets, spinners, error display)
- Domain logic lives in `interview_app.services.*` (guardrails + prompt building + LLM calls)
"""

import streamlit as st

from interview_app.app.controls import UISettings
from interview_app.services.answer_evaluator import evaluate_answer
from interview_app.services.interview_generator import generate_questions
from interview_app.ui.display import (
    show_error,
    show_guardrail_summary,
    show_llm_response,
    show_prompt_debug,
    show_settings_debug,
)
from interview_app.ui.widgets import (
    answer_input,
    job_description_input,
    question_context_input,
)


def render_header() -> None:
    """Render the app title/header at the top of the page."""
    st.title("Interview Practice App")
    st.caption("Generate practice questions and get answer feedback with OpenAI models.")


def render_instructions() -> None:
    """Beginner-friendly usage instructions (collapsed by default)."""
    with st.expander("How to use", expanded=False):
        st.markdown(
            """
- Use the **sidebar** to select an interview type, prompt strategy, and model settings.
- In **Question generation**, provide a job description and click **Generate**.
- In **Answer feedback**, paste a question + your answer and click **Evaluate**.
""".strip()
        )


def render_tabs(settings: UISettings) -> None:
    """
    Render the main UI tabs and wire actions to services.

    Tabs:
    - Question generation → `services.interview_generator.generate_questions`
    - Answer feedback → `services.answer_evaluator.evaluate_answer`
    - Mock interview → placeholder for a future multi-turn flow (session state)
    """
    tab_generate, tab_feedback, tab_mock = st.tabs(["Question generation", "Answer feedback", "Mock interview"])

    with tab_generate:
        st.subheader("Generate interview questions")
        job_description = job_description_input()
        n_questions = st.number_input("Number of questions", min_value=1, max_value=20, value=5, step=1)

        if st.button("Generate questions", type="primary", use_container_width=True):
            try:
                with st.spinner("Generating questions..."):
                    gen_result = generate_questions(
                        interview_type=settings.interview_type,
                        role_title=settings.role_title,
                        seniority=settings.seniority,
                        job_description=job_description,
                        n_questions=int(n_questions),
                        prompt_strategy=settings.prompt_strategy,
                        model=settings.model_preset,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                    )
            except Exception as e:
                # Catch-all so UI doesn't crash; the exception is still shown for debugging.
                show_error(title="Generation failed", body=f"Error: `{type(e).__name__}`\n\n{e}")
            else:
                show_guardrail_summary(guardrails=gen_result.guardrails)
                if not gen_result.ok or gen_result.response is None:
                    show_error(title="Request blocked", body=gen_result.error or "Unknown error.")
                else:
                    show_llm_response(title="Generated questions", response=gen_result.response)
                    if settings.show_debug and gen_result.prompt is not None:
                        show_prompt_debug(
                            system_prompt=gen_result.prompt.system_prompt,
                            user_prompt=gen_result.prompt.user_prompt,
                        )

        if settings.show_debug:
            show_settings_debug(settings=settings, extra={"n_questions": int(n_questions), "job_description_len": len(job_description)})

    with tab_feedback:
        st.subheader("Evaluate an answer")
        question = question_context_input()
        answer = answer_input()

        if st.button("Evaluate answer", type="primary", use_container_width=True):
            try:
                with st.spinner("Evaluating answer..."):
                    eval_result = evaluate_answer(
                        interview_type=settings.interview_type,
                        role_title=settings.role_title,
                        seniority=settings.seniority,
                        question=question,
                        answer=answer,
                        model=settings.model_preset,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                    )
            except Exception as e:
                show_error(title="Evaluation failed", body=f"Error: `{type(e).__name__}`\n\n{e}")
            else:
                show_guardrail_summary(guardrails=eval_result.guardrails)
                if not eval_result.ok or eval_result.response is None:
                    show_error(title="Request blocked", body=eval_result.error or "Unknown error.")
                else:
                    show_llm_response(title="Evaluation", response=eval_result.response)
                    if settings.show_debug and eval_result.system_prompt and eval_result.user_prompt:
                        show_prompt_debug(system_prompt=eval_result.system_prompt, user_prompt=eval_result.user_prompt)

        if settings.show_debug:
            show_settings_debug(
                settings=settings,
                extra={"question_len": len(question), "answer_len": len(answer)},
            )

    with tab_mock:
        st.subheader("Mock interview")
        st.info("Coming soon. This tab will guide you through a multi-turn interview using session state.")

        if settings.show_debug:
            show_settings_debug(settings=settings, extra={"mode": "mock_interview"})

