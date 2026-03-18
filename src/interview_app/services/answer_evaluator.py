from __future__ import annotations

"""
Service: evaluate a candidate answer.

This module powers the "Answer feedback" tab. It performs the same high-level steps
as question generation:
- validate/sanitize inputs (guardrails)
- build prompts (here it's a fixed evaluator prompt, not a strategy template)
- call the OpenAI model once and return a structured response for the UI
"""

from dataclasses import dataclass

from interview_app.llm.openai_client import LLMClient
from interview_app.security.guards import GuardrailResult, protect_system_prompt, run_guardrails
from interview_app.utils.language import language_instruction
from interview_app.utils.types import LLMResponse


@dataclass(frozen=True)
class EvaluateAnswerResult:
    """Return type for `evaluate_answer` (easy to consume from Streamlit)."""

    ok: bool
    response: LLMResponse | None
    error: str | None
    guardrails: dict[str, GuardrailResult]
    system_prompt: str | None
    user_prompt: str | None


def evaluate_answer(
    *,
    interview_type: str,
    role_title: str,
    seniority: str,
    question: str,
    answer: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_language: str = "en",
) -> EvaluateAnswerResult:
    """
    Evaluate a user's answer to an interview question.

    This is intentionally a single-shot evaluator (not a chatbot) to match the
    Sprint-1 project scope.
    """

    # Guardrails: reject empty / overlong / suspicious inputs before calling the model.
    guards: dict[str, GuardrailResult] = {
        "question": run_guardrails(question or "", max_chars=4000),
        "answer": run_guardrails(answer or "", max_chars=8000),
    }
    if not guards["question"].ok:
        return EvaluateAnswerResult(
            ok=False,
            response=None,
            error=guards["question"].reason or "Question rejected by guardrails.",
            guardrails=guards,
            system_prompt=None,
            user_prompt=None,
        )
    if not guards["answer"].ok:
        return EvaluateAnswerResult(
            ok=False,
            response=None,
            error=guards["answer"].reason or "Answer rejected by guardrails.",
            guardrails=guards,
            system_prompt=None,
            user_prompt=None,
        )

    system_prompt = protect_system_prompt(
        _evaluator_system_prompt(response_language=response_language)
    )
    user_prompt = _evaluator_user_prompt(
        interview_type=interview_type,
        role_title=role_title,
        seniority=seniority,
        question=guards["question"].cleaned_text,
        answer=guards["answer"].cleaned_text,
    )

    client = LLMClient(model=model, temperature=temperature, max_tokens=max_tokens)
    resp = client.generate_response(system_prompt=system_prompt, user_prompt=user_prompt)

    return EvaluateAnswerResult(
        ok=True,
        response=resp,
        error=None,
        guardrails=guards,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


def _evaluator_system_prompt(*, response_language: str = "en") -> str:
    base = (
        "You are an expert interview coach. Evaluate the candidate's answer with a focus on clarity, "
        "correctness, structure, and trade-offs. Be specific and actionable."
        "\n\n"
        "Output format:\n"
        "- Score (0-10)\n"
        "- Strengths (bullets)\n"
        "- Gaps / risks (bullets)\n"
        "- Improved answer (concise)\n"
        "- Follow-up questions (3)\n"
    )
    return f"{base}\n\n{language_instruction(response_language)}"


def _evaluator_user_prompt(
    *,
    interview_type: str,
    role_title: str,
    seniority: str,
    question: str,
    answer: str,
) -> str:
    return (
        f"Interview type: {interview_type}\n"
        f"Role: {role_title}\n"
        f"Seniority: {seniority}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Candidate answer:\n"
        f"{answer}\n"
    )

