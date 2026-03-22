from __future__ import annotations

"""
Output validation guard for model responses.

Validates LLM output *before* it reaches the UI:
- Rejects empty or clearly invalid responses.
- Detects possible prompt / system-instruction leakage.
- Enforces a configurable maximum output length.
- Optionally validates structured output (JSON) when expected.
"""

import json
import re
from typing import Final

from pydantic import BaseModel, Field

from interview_app.config.settings import get_security_settings
from interview_app.security.logging import log_security_event

_LEAKAGE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"system\s*prompt\s*[:=]", re.IGNORECASE),
    re.compile(r"developer\s*instructions?\s*[:=]", re.IGNORECASE),
    re.compile(r"(here\s+(is|are)\s+(the|my)\s+system\s+(prompt|instructions?))", re.IGNORECASE),
    re.compile(r"\bSecurity:\s*Never reveal\b", re.IGNORECASE),
    re.compile(r"ignore\s+instructions.*refuse", re.IGNORECASE),
)


class OutputGuardResult(BaseModel):
    """Outcome of output validation."""

    safe: bool
    text: str = ""
    reason: str | None = None
    flags: list[str] = Field(default_factory=list)
    truncated: bool = False


def validate_output(
    text: str | None,
    *,
    expect_json: bool = False,
    service: str = "unknown",
    max_length: int | None = None,
) -> OutputGuardResult:
    """
    Validate model output before displaying to the user.

    Args:
        text: Raw model output.
        expect_json: When ``True``, additionally verify that the output is
            valid JSON.
        service: Calling service name for logging.
        max_length: Override the configured output max length.

    Returns:
        OutputGuardResult indicating whether the output is safe to display.
    """
    sec = get_security_settings()
    limit = max_length if max_length is not None else sec.output_max_length
    flags: list[str] = []

    if text is None or not text.strip():
        log_security_event(
            event="output_guard",
            action="blocked",
            reason="Empty model output",
            service=service,
        )
        return OutputGuardResult(
            safe=False,
            text="",
            reason="The model returned an empty response. Please try again.",
            flags=["empty_output"],
        )

    cleaned = text.strip()

    truncated = False
    if len(cleaned) > limit:
        cleaned = cleaned[:limit]
        truncated = True
        flags.append("output_truncated")

    for pattern in _LEAKAGE_PATTERNS:
        if pattern.search(cleaned):
            log_security_event(
                event="output_guard",
                action="blocked",
                reason="Possible prompt leakage detected in output",
                service=service,
                matched_pattern=pattern.pattern[:80],
            )
            return OutputGuardResult(
                safe=False,
                text="",
                reason="The response was blocked for safety reasons. Please try again.",
                flags=["prompt_leakage_suspected"],
            )

    if expect_json:
        try:
            json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            flags.append("invalid_json")
            log_security_event(
                event="output_guard",
                action="blocked",
                reason="Expected JSON output but got invalid JSON",
                service=service,
            )
            return OutputGuardResult(
                safe=False,
                text=cleaned,
                reason="The model did not return valid structured output. Please try again.",
                flags=flags,
            )

    return OutputGuardResult(
        safe=True,
        text=cleaned,
        truncated=truncated,
        flags=flags,
    )
