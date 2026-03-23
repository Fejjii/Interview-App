"""Defaults used to seed sidebar generation controls (temperature, top-p, max tokens)."""

from __future__ import annotations

from interview_app.app.controls import _session_defaults_for_preset
from interview_app.llm.model_settings import MODEL_PRESETS


def test_session_defaults_match_gpt4o_mini_preset() -> None:
    preset = MODEL_PRESETS["gpt-4o-mini"]
    t, top_p, max_tok = _session_defaults_for_preset(preset)
    assert t == preset.default_temperature
    assert top_p == 1.0  # preset has default_top_p None → 1.0
    assert max_tok == int(preset.default_max_tokens or 800)


def test_session_defaults_gpt4o_uses_explicit_top_p_when_set() -> None:
    from interview_app.llm.model_settings import ModelConfig

    p = ModelConfig(
        name="test",
        default_temperature=0.5,
        default_top_p=0.9,
        default_max_tokens=500,
    )
    t, top_p, max_tok = _session_defaults_for_preset(p)
    assert t == 0.5
    assert top_p == 0.9
    assert max_tok == 500
