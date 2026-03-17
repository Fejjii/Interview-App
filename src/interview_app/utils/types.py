from __future__ import annotations

from pydantic import BaseModel, Field


class LLMUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class LLMResponse(BaseModel):
    text: str = Field(default="")
    model: str | None = None
    usage: LLMUsage | None = None
    raw_response_id: str | None = None

