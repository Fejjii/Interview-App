from __future__ import annotations

"""
Guardrail pipeline orchestrator.

Centralizes the order of all security checks so every service runs them
consistently in a single call:

    Input pipeline (before LLM):
        1. Input validation & sanitization
        2. Secret redaction
        3. Prompt injection detection
        4. Content moderation
        5. Rate limiting (one increment per ``run_input_pipeline`` call with
           ``check_rate=True`` and a non-None ``session_state``; chat turns
           typically consume one unit at the top-level message check, and may
           pass ``skip_session_rate_limit`` to nested services to avoid
           double-counting)

    Output pipeline (after LLM):
        6. Output validation (empty check, length, leakage, optional JSON)
"""

from typing import Any

from pydantic import BaseModel, Field

from interview_app.config.settings import get_security_settings
from interview_app.security.guards import GuardrailResult, run_guardrails
from interview_app.security.moderation import ModerationResult, check_moderation
from interview_app.security.output_guard import OutputGuardResult, validate_output
from interview_app.security.rate_limiter import RateLimitResult, check_rate_limit


class InputPipelineResult(BaseModel):
    """Aggregated result of all pre-LLM security checks on one input field."""

    ok: bool
    cleaned_text: str = ""
    error: str | None = None
    guardrail: GuardrailResult | None = None
    moderation: ModerationResult | None = None
    rate_limit: RateLimitResult | None = None
    flags: list[str] = Field(default_factory=list)


def run_input_pipeline(
    text: str,
    *,
    field_name: str = "input",
    max_chars: int | None = None,
    session_state: dict[str, Any] | None = None,
    check_rate: bool = True,
    service: str = "unknown",
) -> InputPipelineResult:
    """
    Run the full pre-LLM guardrail pipeline on a single input field.

    Checks are executed in order; the pipeline short-circuits on the first
    blocking failure so later checks are not wasted on already-rejected input.

    Args:
        text: Raw user text to validate.
        field_name: Label used in logs and result.
        max_chars: Override for max input length.
        session_state: Mutable dict for rate-limit tracking (e.g. st.session_state).
        check_rate: Whether to include the rate-limit step.
        service: Service name for structured logging.

    Returns:
        InputPipelineResult with ``ok=True`` when all checks pass.
    """
    sec = get_security_settings()
    limit = max_chars if max_chars is not None else sec.max_input_length
    flags: list[str] = []

    # 1-3. Validation + sanitization + secret redaction + injection detection
    guardrail = run_guardrails(text, max_chars=limit, service=service)
    flags.extend(guardrail.flags)

    if not guardrail.ok:
        return InputPipelineResult(
            ok=False,
            cleaned_text=guardrail.cleaned_text,
            error=guardrail.reason or f"Input '{field_name}' rejected by guardrails.",
            guardrail=guardrail,
            flags=flags,
        )

    # 4. Content moderation
    moderation = check_moderation(guardrail.cleaned_text, service=service)
    flags.extend(moderation.flags)

    if not moderation.safe:
        return InputPipelineResult(
            ok=False,
            cleaned_text=guardrail.cleaned_text,
            error=moderation.message,
            guardrail=guardrail,
            moderation=moderation,
            flags=flags,
        )

    # 5. Rate limiting (once per top-level request, not per field)
    rate_result: RateLimitResult | None = None
    if check_rate and session_state is not None:
        rate_result = check_rate_limit(session_state, service=service)
        if not rate_result.allowed:
            return InputPipelineResult(
                ok=False,
                cleaned_text=guardrail.cleaned_text,
                error=rate_result.message,
                guardrail=guardrail,
                moderation=moderation,
                rate_limit=rate_result,
                flags=flags + ["rate_limited"],
            )

    return InputPipelineResult(
        ok=True,
        cleaned_text=guardrail.cleaned_text,
        guardrail=guardrail,
        moderation=moderation,
        rate_limit=rate_result,
        flags=flags,
    )


def run_output_pipeline(
    text: str | None,
    *,
    expect_json: bool = False,
    service: str = "unknown",
    max_length: int | None = None,
) -> OutputGuardResult:
    """
    Run post-LLM output validation.

    Thin wrapper that delegates to ``validate_output`` so callers don't need
    to import the output_guard module directly.
    """
    return validate_output(
        text,
        expect_json=expect_json,
        service=service,
        max_length=max_length,
    )
