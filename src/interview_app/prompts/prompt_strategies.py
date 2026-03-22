from __future__ import annotations

"""
Prompt-building functions ("prompt strategies").

Pure module (no Streamlit, no OpenAI calls): maps interview context to
`system_prompt` + `user_prompt` pairs for `LLMClient`.
"""

from dataclasses import dataclass

from interview_app.prompts.personas import get_persona_prompt
from interview_app.prompts.prompt_templates import load_template_text
from interview_app.utils.language import language_instruction


@dataclass(frozen=True)
class PromptBuildResult:
    """A fully-built prompt ready to send to `LLMClient`."""

    system_prompt: str
    user_prompt: str
    template_name: str


def build_zero_shot_prompt(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
    job_description: str = "",
    n_questions: int = 5,
    response_language: str = "en",
    difficulty: str = "Medium",
    persona: str = "Hiring Manager",
) -> PromptBuildResult:
    """Build a direct, instruction-only (zero-shot) prompt."""
    template = load_template_text("zero_shot")
    user_prompt = _format_template(
        template,
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=_normalize_block(job_description),
        n_questions=n_questions,
        difficulty=difficulty,
        persona=persona,
    )
    system_prompt = _system_prompt_for(
        "zero_shot", response_language=response_language, persona=persona
    )
    return PromptBuildResult(
        system_prompt=system_prompt, user_prompt=user_prompt, template_name="zero_shot"
    )


def build_few_shot_prompt(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
    job_description: str = "",
    n_questions: int = 5,
    response_language: str = "en",
    difficulty: str = "Medium",
    persona: str = "Hiring Manager",
) -> PromptBuildResult:
    """Build a prompt that includes examples (few-shot) to steer format/quality."""
    template = load_template_text("few_shot")
    user_prompt = _format_template(
        template,
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=_normalize_block(job_description),
        n_questions=n_questions,
        difficulty=difficulty,
        persona=persona,
    )
    system_prompt = _system_prompt_for(
        "few_shot", response_language=response_language, persona=persona
    )
    return PromptBuildResult(
        system_prompt=system_prompt, user_prompt=user_prompt, template_name="few_shot"
    )


def build_chain_of_thought_prompt(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
    job_description: str = "",
    n_questions: int = 5,
    response_language: str = "en",
    difficulty: str = "Medium",
    persona: str = "Hiring Manager",
) -> PromptBuildResult:
    """
    Build a prompt that encourages step-by-step reasoning.

    Note: The system prompt explicitly instructs the model not to reveal hidden reasoning.
    """
    template = load_template_text("chain_of_thought")
    user_prompt = _format_template(
        template,
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=_normalize_block(job_description),
        n_questions=n_questions,
        difficulty=difficulty,
        persona=persona,
    )
    system_prompt = _system_prompt_for(
        "chain_of_thought", response_language=response_language, persona=persona
    )
    return PromptBuildResult(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        template_name="chain_of_thought",
    )


def build_structured_output_prompt(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
    job_description: str = "",
    n_questions: int = 5,
    response_language: str = "en",
    difficulty: str = "Medium",
    persona: str = "Hiring Manager",
) -> PromptBuildResult:
    """Build a prompt that asks for machine-readable output (JSON)."""
    template = load_template_text("structured_output")
    user_prompt = _format_template(
        template,
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=_normalize_block(job_description),
        n_questions=n_questions,
        difficulty=difficulty,
        persona=persona,
    )
    system_prompt = _system_prompt_for(
        "structured_output", response_language=response_language, persona=persona
    )
    return PromptBuildResult(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        template_name="structured_output",
    )


def build_role_based_prompt(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
    job_description: str = "",
    n_questions: int = 5,
    response_language: str = "en",
    difficulty: str = "Medium",
    persona: str = "Hiring Manager",
) -> PromptBuildResult:
    """Build a prompt that sets a strong interviewer persona (role-based prompting)."""
    template = load_template_text("role_based")
    user_prompt = _format_template(
        template,
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
        job_description=_normalize_block(job_description),
        n_questions=n_questions,
        difficulty=difficulty,
        persona=persona,
    )
    system_prompt = _system_prompt_for(
        "role_based", response_language=response_language, persona=persona
    )
    return PromptBuildResult(
        system_prompt=system_prompt, user_prompt=user_prompt, template_name="role_based"
    )


def _system_prompt_for(
    strategy: str,
    *,
    response_language: str = "en",
    persona: str = "Hiring Manager",
) -> str:
    """
    Return a distinct system prompt per technique.
    Appends persona tone and language instruction.
    """

    base = (
        "You are an AI interview assistant helping a candidate prepare for a realistic hiring "
        "conversation. Follow instructions precisely, stay role-relevant, and avoid inventing "
        "employer-specific facts that were not provided."
    )

    match strategy:
        case "zero_shot":
            tech = "Technique: Zero-shot. Use direct instructions; do not add extra commentary."
        case "few_shot":
            tech = "Technique: Few-shot. Use the provided examples as a style and depth guide."
        case "chain_of_thought":
            tech = (
                "Technique: Chain-of-thought (private). Think step-by-step internally, "
                "but do not reveal hidden reasoning—output only the final questions."
            )
        case "structured_output":
            tech = (
                "Technique: Structured output. Return valid JSON exactly matching the requested schema. "
                "No markdown, no extra keys, no trailing commentary."
            )
        case "role_based":
            tech = "Technique: Role-based. Maintain a consistent interviewer persona and tone."
        case _:
            tech = ""

    prompt = f"{base}\n\n{tech}" if tech else base
    persona_fragment = get_persona_prompt(persona)
    prompt = f"{prompt}\n\nInterviewer tone: {persona_fragment}"
    return f"{prompt}\n\n{language_instruction(response_language)}"


def _normalize_block(text: str) -> str:
    """Normalize optional multi-line blocks so templates can assume a value exists."""
    t = (text or "").strip()
    return t if t else "(none)"


def _format_template(template: str, **kwargs: object) -> str:
    return template.format(**kwargs)
