from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration defaults for a given model preset."""

    name: str = Field(description="OpenAI model name, e.g. 'gpt-4o-mini'.")
    default_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    default_top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    default_max_tokens: int | None = Field(default=800, ge=1)


ModelPresetKey = Literal[
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
]


MODEL_PRESETS: dict[ModelPresetKey, ModelConfig] = {
    "gpt-4.1": ModelConfig(name="gpt-4.1", default_temperature=0.2, default_max_tokens=1200),
    "gpt-4.1-mini": ModelConfig(name="gpt-4.1-mini", default_temperature=0.2, default_max_tokens=1000),
    "gpt-4.1-nano": ModelConfig(name="gpt-4.1-nano", default_temperature=0.2, default_max_tokens=900),
    "gpt-4o": ModelConfig(name="gpt-4o", default_temperature=0.2, default_max_tokens=1200),
    "gpt-4o-mini": ModelConfig(name="gpt-4o-mini", default_temperature=0.2, default_max_tokens=1000),
}


def get_model_config(key: str) -> ModelConfig:
    """
    Get a model preset by key.

    Raises:
        KeyError: if the key is not a known preset.
    """

    return MODEL_PRESETS[key]  # type: ignore[index]

