"""Composable prompt strategies for interview question generation (zero/few-shot, CoT, etc.).

Pure functions: no Streamlit imports, no network I/O. Each ``build_*`` function
returns ``PromptBuildResult`` (system + user strings) using templates from
``prompt_templates`` and persona text from ``personas``.

Consumed exclusively by ``services/interview_generator`` and unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass

from interview_app.prompts.few_shot_examples import build_few_shot_demonstration_block
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
        "zero_shot",
        response_language=response_language,
        persona=persona,
        include_persona=False,
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
    few_shot_demonstrations = build_few_shot_demonstration_block(
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
    )
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
        few_shot_demonstrations=few_shot_demonstrations,
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
    persona_identity = _role_based_identity_line(
        persona=persona,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
    )
    persona_behavior = get_persona_prompt(persona)
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
        persona_identity=persona_identity,
        persona_behavior=persona_behavior,
    )
    system_prompt = _system_prompt_for(
        "role_based", response_language=response_language, persona=persona
    )
    return PromptBuildResult(
        system_prompt=system_prompt, user_prompt=user_prompt, template_name="role_based"
    )


def _role_based_identity_line(
    *,
    persona: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
) -> str:
    """Strong interviewer anchor for role-based prompting (user prompt body)."""
    return (
        f"You are **{persona}** conducting the **{interview_round}** for a candidate "
        f"targeting **{role_title}** ({seniority}). "
        f"This round should stress **{interview_focus}**. "
        "Stay in character: your questions should sound like a real interviewer, not a study guide."
    )


def _system_prompt_for(
    strategy: str,
    *,
    response_language: str = "en",
    persona: str = "Hiring Manager",
    include_persona: bool = True,
) -> str:
    """
    Return a distinct system prompt per technique.
    Appends persona tone (except zero-shot) and language instruction.
    """

    base = (
        "You are an AI interview assistant helping a candidate prepare for a realistic hiring "
        "conversation. Follow instructions precisely, stay role-relevant, and avoid inventing "
        "employer-specific facts that were not provided."
    )

    match strategy:
        case "zero_shot":
            tech = (
                "Technique: Zero-shot. Direct instructions only in the user message—no separate "
                "worked examples, no chain-of-thought in the reply. Output only the requested questions."
            )
        case "few_shot":
            tech = (
                "Technique: Few-shot. Treat the provided demonstrations as pattern, depth, and tone "
                "guides. Generate **new** questions in the same style; do not copy or lightly paraphrase them."
            )
        case "chain_of_thought":
            tech = (
                "Technique: Chain-of-thought (internal only). Before writing anything visible, privately "
                "work through—in order—(1) role priorities implied by the role title, seniority, and job "
                "description, (2) key competencies to test for the stated interview focus and round, "
                "(3) appropriate depth for seniority and round, (4) a brief plan for the requested number "
                "of questions. Then output **only** a numbered list of interview questions. Do not output "
                "steps, labels, analysis, or chain-of-thought text."
            )
        case "structured_output":
            tech = (
                "Technique: Structured output. Return **valid JSON only**, exactly matching the schema "
                "in the user message. No markdown fences, no prose before or after the JSON."
            )
        case "role_based":
            tech = (
                "Technique: Role-based prompting. The user message defines a concrete interviewer "
                "identity and behavior—honor it consistently in every line you output."
            )
        case _:
            tech = ""

    prompt = f"{base}\n\n{tech}" if tech else base
    if include_persona:
        persona_fragment = get_persona_prompt(persona)
        prompt = f"{prompt}\n\nInterviewer tone (calibration): {persona_fragment}"
    return f"{prompt}\n\n{language_instruction(response_language)}"


def _normalize_block(text: str) -> str:
    """Normalize optional multi-line blocks so templates can assume a value exists."""
    t = (text or "").strip()
    return t if t else "(none)"


def _format_template(template: str, **kwargs: object) -> str:
    return template.format(**kwargs)
