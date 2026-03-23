"""Cross-cutting Pydantic models and DTOs (LLM, chat, sessions, evaluation).

Keeps services and UI decoupled from OpenAI SDK response objects. Stable shapes
here make unit tests straightforward.

Inputs/outputs: constructed by ``llm/openai_client``, ``services/*``, and
``storage/sessions``; consumed by Streamlit display helpers and tests.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


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


class ChatMessage(BaseModel):
    """Single chat turn (user or assistant)."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(default="")


class EvaluationResult(BaseModel):
    """Structured evaluation from answer_evaluator (score, criteria, critique)."""

    score: int = Field(default=0, ge=0, le=10)
    criteria_met: list[str] = Field(default_factory=list)
    criteria_missing: list[str] = Field(default_factory=list)
    critique: str = Field(default="")
    improved_answer: str = Field(default="")
    follow_ups: list[str] = Field(default_factory=list)


class SessionMeta(BaseModel):
    """Metadata for a saved session (config snapshot for replay)."""

    id: str = Field(default="")
    created_at: str = Field(default="")
    role_category: str = Field(default="")
    role_title: str = Field(default="")
    seniority: str = Field(default="")
    difficulty: str = Field(default="")
    difficulty_mode: str = Field(default="")
    interview_round: str = Field(default="")
    interview_focus: str = Field(default="")
    persona: str = Field(default="")
    title: str = Field(default="")
    # Legacy key from older sessions (maps to interview_focus when loading)
    interview_type: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def _legacy_interview_type(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if not out.get("interview_focus") and out.get("interview_type"):
            out["interview_focus"] = out["interview_type"]
        return out

