from __future__ import annotations

"""
Shared data models (types) used across the app.

These are intentionally small and stable:
- services and UI can pass around `LLMResponse` without depending on OpenAI SDK objects
- tests can assert on simple Pydantic models
"""

from pydantic import BaseModel, Field


class LLMUsage(BaseModel):
    """Token usage metadata (when available from the OpenAI response)."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class LLMResponse(BaseModel):
    """Normalized response returned by `LLMClient`."""

    text: str = Field(default="")
    model: str | None = None
    usage: LLMUsage | None = None
    raw_response_id: str | None = None

