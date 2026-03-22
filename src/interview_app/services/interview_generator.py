from __future__ import annotations

"""
Service: generate interview questions.

This module is the "domain layer" for the Question generation tab.
It translates UI inputs into:
- validated/sanitized text (guardrails via the security pipeline)
- a chosen prompt strategy (prompt-building)
- a single OpenAI call (LLM client)

The Streamlit UI calls `generate_questions(...)` directly and then renders either:
- a blocked request (guardrail failure), or
- an `LLMResponse` with optional prompt debug output.
"""

from dataclasses import dataclass
from typing import Any, Callable

from interview_app.app.interview_form_config import truncate_job_description, validate_role_title
from interview_app.llm.openai_client import LLMClient
from interview_app.prompts import prompt_strategies
from interview_app.prompts.prompt_strategies import PromptBuildResult
from interview_app.security.guards import GuardrailResult, protect_system_prompt
from interview_app.security.pipeline import run_input_pipeline, run_output_pipeline
from interview_app.utils.errors import safe_user_message
from interview_app.utils.types import LLMResponse


_SERVICE_NAME = "interview_generator"


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
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
    job_description: str,
    n_questions: int,
    prompt_strategy: str,
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float | None = None,
    response_language: str = "en",
    difficulty: str = "Medium",
    persona: str = "Hiring Manager",
    session_state: dict[str, Any] | None = None,
) -> GenerateQuestionsResult:
    """
    Generate interview questions using a selected prompt strategy.

    This is the main "happy path" service used by the Streamlit UI.
    """

    guards: dict[str, GuardrailResult] = {}

    ok_title, role_trimmed = validate_role_title(role_title)
    if not ok_title:
        return GenerateQuestionsResult(
            ok=False,
            response=None,
            error="Please enter a role title.",
            guardrails=guards,
            prompt=None,
        )

    # --- Input pipeline: validation + sanitization + moderation + rate limit ---
    role_pipe = run_input_pipeline(
        role_trimmed,
        field_name="role_title",
        max_chars=200,
        session_state=session_state,
        check_rate=True,
        service=_SERVICE_NAME,
    )
    if role_pipe.guardrail:
        guards["role_title"] = role_pipe.guardrail
    if not role_pipe.ok:
        return GenerateQuestionsResult(
            ok=False,
            response=None,
            error=role_pipe.error or "Invalid role title.",
            guardrails=guards,
            prompt=None,
        )

    jd_text = truncate_job_description(job_description)
    jd_pipe = run_input_pipeline(
        jd_text,
        field_name="job_description",
        max_chars=8000,
        session_state=None,
        check_rate=False,
        service=_SERVICE_NAME,
    )
    if jd_pipe.guardrail:
        guards["job_description"] = jd_pipe.guardrail
    if jd_text and not jd_pipe.ok:
        return GenerateQuestionsResult(
            ok=False,
            response=None,
            error=jd_pipe.error or "Job description rejected by guardrails.",
            guardrails=guards,
            prompt=None,
        )

    prompt = _build_prompt(
        prompt_strategy=prompt_strategy,
        role_category=role_category,
        role_title=role_pipe.cleaned_text,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=jd_pipe.cleaned_text if jd_text else "",
        n_questions=n_questions,
        response_language=response_language,
        difficulty=difficulty,
        persona=persona,
    )

    system_prompt = protect_system_prompt(prompt.system_prompt)

    try:
        client = LLMClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        resp = client.generate_response(
            system_prompt=system_prompt,
            user_prompt=prompt.user_prompt,
            top_p=top_p,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        return GenerateQuestionsResult(
            ok=False,
            response=None,
            error=safe_user_message(exc),
            guardrails=guards,
            prompt=None,
        )

    # --- Output pipeline: validate model response ---
    output_check = run_output_pipeline(resp.text, service=_SERVICE_NAME)
    if not output_check.safe:
        return GenerateQuestionsResult(
            ok=False,
            response=None,
            error=output_check.reason or "Model output rejected.",
            guardrails=guards,
            prompt=None,
        )

    safe_resp = LLMResponse(
        text=output_check.text,
        model=resp.model,
        usage=resp.usage,
        raw_response_id=resp.raw_response_id,
    )

    return GenerateQuestionsResult(
        ok=True,
        response=safe_resp,
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
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
    job_description: str,
    n_questions: int,
    response_language: str = "en",
    difficulty: str = "Medium",
    persona: str = "Hiring Manager",
) -> PromptBuildResult:
    """
    Dispatch to the correct prompt-builder function by strategy name.
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
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=job_description,
        n_questions=n_questions,
        response_language=response_language,
        difficulty=difficulty,
        persona=persona,
    )
