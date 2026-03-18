from __future__ import annotations

"""
Unit tests for prompt strategies (`interview_app.prompts.prompt_strategies`).

Goal:
- verify each strategy returns non-empty system + user prompts
- sanity-check that the structured-output strategy actually asks for JSON
"""

from interview_app.prompts.prompt_strategies import (
    build_chain_of_thought_prompt,
    build_few_shot_prompt,
    build_role_based_prompt,
    build_structured_output_prompt,
    build_zero_shot_prompt,
)


def test_prompt_strategies_return_non_empty_prompts() -> None:
    """All strategies should return usable prompt strings."""
    common = {
        "interview_type": "Behavioral",
        "role_title": "Software Engineer",
        "seniority": "Senior",
        "job_description": "Build APIs; collaborate with product; write tests.",
        "n_questions": 5,
    }

    results = [
        build_zero_shot_prompt(**common),
        build_few_shot_prompt(**common),
        build_chain_of_thought_prompt(**common),
        build_structured_output_prompt(**common),
        build_role_based_prompt(**common),
    ]

    for res in results:
        assert res.system_prompt.strip()
        assert res.user_prompt.strip()
        assert res.template_name


def test_structured_output_template_mentions_json() -> None:
    """Structured output strategy should request JSON (for easier parsing)."""
    res = build_structured_output_prompt(
        interview_type="System design",
        role_title="Backend Engineer",
        seniority="Mid",
        job_description="Design scalable APIs.",
        n_questions=3,
    )
    assert "json" in res.user_prompt.lower()

