from __future__ import annotations

"""
Model presets used by the UI.

The Streamlit sidebar lets users choose a "model preset" key (e.g. `gpt-4o-mini`).
Each preset provides defaults for:
- temperature
- top_p (optional)
- max_tokens (optional)

The `LLMClient` can consume these presets to pick sane defaults without forcing the UI
to hardcode per-model numbers.
"""

from typing import Literal, TypeGuard

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration defaults for a given model preset."""

    name: str = Field(description="OpenAI model name, e.g. 'gpt-4o-mini'.")
    default_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    default_top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    default_max_tokens: int | None = Field(default=800, ge=1)


ModelPresetKey = Literal[
    "gpt-4o",
    "gpt-4o-mini",
]


MODEL_PRESETS: dict[ModelPresetKey, ModelConfig] = {
    "gpt-4o": ModelConfig(name="gpt-4o", default_temperature=0.2, default_max_tokens=1200),
    "gpt-4o-mini": ModelConfig(name="gpt-4o-mini", default_temperature=0.2, default_max_tokens=1000),
}


def is_model_preset_key(key: str) -> TypeGuard[ModelPresetKey]:
    """Return True if `key` is one of the known `MODEL_PRESETS` keys."""
    return key in MODEL_PRESETS


def get_model_config(key: str) -> ModelConfig:
    """
    Get a model preset by key.

    Raises:
        KeyError: if the key is not a known preset.
    """

    return MODEL_PRESETS[key]  # type: ignore[index]

