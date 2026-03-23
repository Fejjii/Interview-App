from __future__ import annotations

import pytest

from interview_app.cv.json_utils import extract_json_object, parse_llm_json_model
from interview_app.cv.models import CVStructuredExtraction


def test_extract_json_object_from_fence() -> None:
    raw = 'Here is JSON:\n```json\n{"profile_summary": "x", "skills": []}\n```'
    out = extract_json_object(raw)
    assert '"profile_summary"' in out


def test_parse_llm_json_model_roundtrip() -> None:
    raw = '{"profile_summary": "Dev", "skills": ["Python"], "tools_technologies": [], "work_experience": [], "projects": [], "education": [], "certifications": [], "detected_roles": ["Engineer"]}'
    model = parse_llm_json_model(raw, CVStructuredExtraction)
    assert model.profile_summary == "Dev"
    assert "Python" in model.skills


def test_parse_llm_json_model_invalid() -> None:
    with pytest.raises(ValueError):
        parse_llm_json_model("not json", CVStructuredExtraction)
