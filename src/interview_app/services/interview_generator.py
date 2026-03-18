from __future__ import annotations

"""
Service: generate interview questions.

This module is the "domain layer" for the Question generation tab.
It translates UI inputs into:
- validated/sanitized text (guardrails)
- a chosen prompt strategy (prompt-building)
- a single OpenAI call (LLM client)

The Streamlit UI calls `generate_questions(...)` directly and then renders either:
- a blocked request (guardrail failure), or
- an `LLMResponse` with optional prompt debug output.
"""

from dataclasses import dataclass
from typing import Callable

from interview_app.llm.openai_client import LLMClient
from interview_app.prompts import prompt_strategies
from interview_app.prompts.prompt_strategies import PromptBuildResult
from interview_app.security.guards import GuardrailResult, protect_system_prompt, run_guardrails
from interview_app.utils.types import LLMResponse


@dataclass(frozen=True)
class GenerateQuestionsResult:
    """Return type for `generate_questions` (easy to consume from Streamlit)."""

    ok: bool
    response: LLMResponse | None
    error: str | None
    guardrails: dict[str, GuardrailResult]
    prompt: PromptBuildResult | None


def generate_questions(
    *,
    interview_type: str,
    role_title: str,
    seniority: str,
    job_description: str,
    n_questions: int,
    prompt_strategy: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_language: str = "en",
) -> GenerateQuestionsResult:
    """
    Generate interview questions using a selected prompt strategy.

    This is the main "happy path" service used by the Streamlit UI.
    """

    # Guardrails run first so we never send unsafe or malformed content to the model.
    # Each input gets an independent result so the UI can show a clear summary.

    guards: dict[str, GuardrailResult] = {
        "job_description": run_guardrails(job_description or "", max_chars=8000),
        "role_title": run_guardrails(role_title or "", max_chars=200),
    }
    if not guards["role_title"].ok:
        return GenerateQuestionsResult(
            ok=False,
            response=None,
            error=guards["role_title"].reason or "Invalid role title.",
            guardrails=guards,
            prompt=None,
        )
    if job_description and not guards["job_description"].ok:
        return GenerateQuestionsResult(
            ok=False,
            response=None,
            error=guards["job_description"].reason or "Job description rejected by guardrails.",
            guardrails=guards,
            prompt=None,
        )

    prompt = _build_prompt(
        prompt_strategy=prompt_strategy,
        interview_type=interview_type,
        role_title=guards["role_title"].cleaned_text,
        seniority=seniority,
        job_description=guards["job_description"].cleaned_text if job_description else "",
        n_questions=n_questions,
        response_language=response_language,
    )

    # Add a defensive instruction that the model must not reveal system/developer prompts.
    system_prompt = protect_system_prompt(prompt.system_prompt)
    client = LLMClient(model=model, temperature=temperature, max_tokens=max_tokens)
    resp = client.generate_response(system_prompt=system_prompt, user_prompt=prompt.user_prompt)

    return GenerateQuestionsResult(
        ok=True,
        response=resp,
        error=None,
        guardrails=guards,
        prompt=PromptBuildResult(
            system_prompt=system_prompt,
            user_prompt=prompt.user_prompt,
            template_name=prompt.template_name,
        ),
    )


def _build_prompt(
    *,
    prompt_strategy: str,
    interview_type: str,
    role_title: str,
    seniority: str,
    job_description: str,
    n_questions: int,
    response_language: str = "en",
) -> PromptBuildResult:
    """
    Dispatch to the correct prompt-builder function by strategy name.

    Keeping this mapping here makes it explicit which strategies are supported by the UI.
    """
    builders: dict[str, Callable[..., PromptBuildResult]] = {
        "zero_shot": prompt_strategies.build_zero_shot_prompt,
        "few_shot": prompt_strategies.build_few_shot_prompt,
        "chain_of_thought": prompt_strategies.build_chain_of_thought_prompt,
        "structured_output": prompt_strategies.build_structured_output_prompt,
        "role_based": prompt_strategies.build_role_based_prompt,
    }
    builder = builders.get(prompt_strategy)
    if builder is None:
        raise ValueError(f"Unknown prompt strategy: {prompt_strategy!r}")

    return builder(
        interview_type=interview_type,
        role_title=role_title,
        seniority=seniority,
        job_description=job_description,
        n_questions=n_questions,
        response_language=response_language,
    )

