"""Seniority calibration must separate Junior vs Senior depth in question-generation prompts."""

from __future__ import annotations

from interview_app.prompts.prompt_strategies import build_zero_shot_prompt


def _base() -> dict[str, object]:
    return {
        "role_category": "Data Engineering",
        "role_title": "Data Engineer",
        "interview_round": "Technical Interview",
        "interview_focus": "Technical Knowledge",
        "job_description": "Pipelines, Snowflake, orchestration.",
        "n_questions": 5,
        "response_language": "en",
        "difficulty": "Medium",
        "persona": "Hiring Manager",
    }


def test_junior_prompt_emphasizes_foundations() -> None:
    kwargs = {**_base(), "seniority": "Entry-Level / Junior"}
    up = build_zero_shot_prompt(**kwargs).user_prompt.lower()
    assert "entry-level / junior" in up or "junior" in up
    assert "foundational" in up or "basic sql" in up or "definitions" in up
    assert "avoid" in up and "platform" in up  # avoid org-wide platform essays


def test_senior_prompt_emphasizes_architecture_and_scale() -> None:
    kwargs = {**_base(), "seniority": "Senior"}
    up = build_zero_shot_prompt(**kwargs).user_prompt.lower()
    assert "senior)" in up or "calibration (senior" in up
    for needle in (
        "architecture",
        "trade-off",
        "scalab",
        "schema evolution",
        "observability",
        "fault tolerance",
    ):
        assert needle in up, f"missing {needle!r}"


def test_senior_data_engineer_style_cues_present() -> None:
    kwargs = {**_base(), "seniority": "Senior", "role_category": "Data Engineering"}
    up = build_zero_shot_prompt(**kwargs).user_prompt
    assert "Snowflake" in up or "BigQuery" in up
    assert "idempotent" in up.lower() or "quality" in up.lower()


def test_junior_and_senior_calibration_blocks_differ_strongly() -> None:
    j = build_zero_shot_prompt(**{**_base(), "seniority": "Entry-Level / Junior"}).user_prompt
    s = build_zero_shot_prompt(**{**_base(), "seniority": "Senior"}).user_prompt
    j_low = j.lower()
    s_low = s.lower()
    assert "foundational" in j_low or "basic" in j_low
    assert "system thinking" in s_low or "trade-off" in s_low
    # Shared role line should still ground both
    assert "Data Engineering" in j and "Data Engineering" in s


def test_chain_of_thought_system_tail_matches_seniority() -> None:
    from interview_app.prompts.prompt_strategies import build_chain_of_thought_prompt

    c_j = build_chain_of_thought_prompt(**{**_base(), "seniority": "Entry-Level / Junior"})
    c_s = build_chain_of_thought_prompt(**{**_base(), "seniority": "Senior"})
    assert "junior (internal)" in c_j.system_prompt.lower()
    assert "senior / staff (internal)" in c_s.system_prompt.lower()
