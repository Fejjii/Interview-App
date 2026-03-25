"""Model preset registry, resolution, and wiring into services (no Streamlit)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from interview_app.app.interview_form_config import infer_difficulty_from_context
from interview_app.app.ui_settings import UISettings
from interview_app.llm.model_settings import (
    DEFAULT_MODEL_PRESET_KEY,
    MODEL_PRESET_SIDEBAR_OPTIONS,
    MODEL_PRESETS,
    get_model_config,
    is_model_preset_key,
    resolve_openai_model_id,
    sidebar_label_for_preset,
)
from interview_app.services.chat_service import mock_llm_config_from_settings
from interview_app.services.interview_generator import generate_questions


def test_all_sidebar_presets_exist_in_registry() -> None:
    keys = [k for _, k in MODEL_PRESET_SIDEBAR_OPTIONS]
    assert set(keys) == set(MODEL_PRESETS.keys())
    assert DEFAULT_MODEL_PRESET_KEY in MODEL_PRESETS


def test_resolve_openai_model_id_matches_preset_name() -> None:
    for key in MODEL_PRESETS:
        assert resolve_openai_model_id(key) == MODEL_PRESETS[key].name


def test_resolve_openai_model_id_passes_through_unknown() -> None:
    assert resolve_openai_model_id("custom-model-xyz") == "custom-model-xyz"


def test_is_model_preset_key() -> None:
    assert is_model_preset_key("gpt-4.1-mini")
    assert not is_model_preset_key("not-a-preset")


def test_sidebar_label_for_preset() -> None:
    assert "GPT" in sidebar_label_for_preset("gpt-4o-mini")
    assert sidebar_label_for_preset("unknown") == "unknown"


def test_mock_llm_config_resolved_model_matches_registry() -> None:
    settings = UISettings(
        role_category="Software Engineering",
        role_title="Eng",
        seniority="Mid-Level",
        interview_round="Technical Interview",
        interview_focus="Technical Knowledge",
        job_description="",
        persona="Hiring Manager",
        question_difficulty_mode="Auto",
        effective_question_difficulty="Medium",
        prompt_strategy="zero_shot",
        model_preset="gpt-4.1-nano",
        temperature=0.3,
        top_p=0.95,
        max_tokens=900,
        show_debug=False,
        response_language="en",
        usage_mode="demo",
        byo_key_hint=None,
    )
    cfg = mock_llm_config_from_settings(settings)
    assert cfg.model_preset == "gpt-4.1-nano"
    assert cfg.resolved_model_name == get_model_config("gpt-4.1-nano").name


def test_infer_difficulty_auto_unchanged() -> None:
    d_auto = infer_difficulty_from_context(
        seniority="Mid-Level",
        interview_round="Technical Interview",
        manual_mode="Auto",
    )
    assert d_auto == "Medium"


def test_infer_difficulty_manual_overrides_auto() -> None:
    assert (
        infer_difficulty_from_context(
            seniority="Mid-Level",
            interview_round="Technical Interview",
            manual_mode="Easy",
        )
        == "Easy"
    )


def test_generate_questions_uses_resolved_model_in_api_call() -> None:
    """Preset key in UI maps to the same id sent to OpenAI for supported presets."""

    def fake_pipeline_ok(*args: object, **kwargs: object) -> MagicMock:
        text = str(args[0]) if args else ""
        r = MagicMock()
        r.ok = True
        r.cleaned_text = text
        r.guardrail = None
        r.error = None
        return r

    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="1. Test question?"))]
    mock_resp.usage = None
    mock_resp.model = "gpt-4.1"
    mock_resp.id = "x"

    with patch(
        "interview_app.services.interview_generator.run_input_pipeline",
        side_effect=fake_pipeline_ok,
    ):
        with patch("interview_app.services.interview_generator.run_output_pipeline") as out:
            out.return_value = MagicMock(safe=True, text="1. Test question?")
            with patch("interview_app.llm.openai_client.OpenAI") as oa:
                inst = MagicMock()
                oa.return_value = inst
                inst.chat.completions.create.return_value = mock_resp
                result = generate_questions(
                    role_category="Software Engineering",
                    role_title="Backend Engineer",
                    seniority="Senior",
                    interview_round="Technical Interview",
                    interview_focus="Technical Knowledge",
                    job_description="",
                    n_questions=1,
                    prompt_strategy="zero_shot",
                    model="gpt-4.1",
                    temperature=0.2,
                    max_tokens=500,
                    top_p=1.0,
                    openai_api_key="sk-test123456789012345678901234567890",
                )
    assert result.ok
    call_kw = inst.chat.completions.create.call_args.kwargs
    assert call_kw["model"] == "gpt-4.1"


def test_chat_turn_result_has_optional_llm_debug() -> None:
    from interview_app.services.chat_service import ChatTurnResult

    r = ChatTurnResult(assistant_message="hi")
    assert r.llm_debug is None
