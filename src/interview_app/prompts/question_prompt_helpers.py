"""Shared helpers for interview question prompt strategies.

Keeps diversity / quality instructions and seniority-aware fragments out of the
main strategy module so templates stay readable and tests can import constants.
"""

from __future__ import annotations

# Visible section headers the model may echo—keep out of user prompts; we use plain paragraphs.

_SENIORITY_STAFF: frozenset[str] = frozenset(
    {
        "Lead / Staff",
        "Principal / Architect",
        "Director",
        "Manager",  # often accountable for trade-offs/incidents in interviews
    }
)


def seniority_band(seniority: str) -> str:
    """
    Coarse band for example depth and CoT expectations.

    Bands: ``junior`` | ``mid`` | ``senior`` | ``staff_plus``.
    """
    s = (seniority or "").strip()
    if not s:
        return "mid"
    if "Entry" in s or "Junior" in s:
        return "junior"
    if s in _SENIORITY_STAFF or "Principal" in s or "Architect" in s or "Staff" in s or "Lead" in s:
        return "staff_plus"
    if s == "Senior":
        return "senior"
    return "mid"


def diversity_block_zero_shot(*, n_questions: int, seniority: str) -> str:
    """Quality + variety constraints appropriate for direct baseline questions."""
    band = seniority_band(seniority)
    depth = (
        "Keep each question **one clear ask** (classic interview style). "
        "Avoid long multi-paragraph hypotheticals."
        if band == "junior"
        else "Keep each question focused; you may use a **short** concrete setup when it clarifies the ask."
    )
    return (
        f"Quality bar: produce **{n_questions}** distinct questions. {depth}\n"
        "Spread topics: do **not** ask the same idea twice with different wording.\n"
        "Avoid pure textbook definitions unless difficulty is Easy; prefer questions a real interviewer would ask.\n"
        "Include a mix of: conceptual understanding, practical application, and (where natural) a light trade-off or constraint."
        + (
            "\nFor senior/staff levels, at least one question should validate depth of ownership or judgment—"
            "without turning every item into a mini design doc."
            if band in {"senior", "staff_plus"}
            else ""
        )
    )


def diversity_block_few_shot(*, n_questions: int, seniority: str) -> str:
    """Steer toward realistic, scenario-led interviewer voice (matches exemplars)."""
    band = seniority_band(seniority)
    scenario = (
        "Most questions should sound like a **live interviewer**: concrete situations, clarifying constraints, "
        "and realistic stakes."
        if band != "junior"
        else "Prefer **short workplace scenarios** (one or two sentences) before the core ask when it helps realism."
    )
    return (
        f"Generate **{n_questions}** **new** questions. {scenario}\n"
        "Match the **style** of the examples (scenario-led, interviewer-like, specific)—but do **not** copy or "
        "lightly paraphrase them; invent fresh situations tied to the role title, focus, and job description.\n"
        "Vary across items: behavioral signals, technical depth, debugging/investigation, and prioritization—"
        "as appropriate to the interview focus.\n"
        "No duplicate themes; avoid generic filler (“Tell me about yourself”, “What is X definition only”)."
    )


def diversity_block_chain_of_thought(*, n_questions: int, seniority: str) -> str:
    """User-visible depth expectations after internal reasoning (CoT stays in system prompt)."""
    band = seniority_band(seniority)
    if band == "junior":
        ratio = "At least half"
        depth = (
            "questions should include a **small realistic constraint** (time, data missing, ambiguity) "
            "and ask **how** the candidate would proceed—not just **what** a term means."
        )
    elif band == "mid":
        ratio = "At least half"
        depth = (
            "questions should be **situation-based** (production-like), and several should surface **trade-offs**, "
            "**risks**, or **prioritization**."
        )
    else:
        ratio = "At least two thirds"
        depth = (
            "questions should be **multi-stakeholder** or **multi-constraint** scenarios that probe **system thinking**: "
            "scale, reliability, **data quality under change**, **incident response**, cost/latency, and architectural "
            "or process trade-offs. Favor questions that reveal **how** the candidate prioritizes and **why**."
        )
    return (
        f"Output goals: **{n_questions}** numbered questions only. {ratio} of the {depth}\n"
        "Favor prompts that require the candidate to **compare options**, **defend priorities**, or **walk through "
        "debugging/design under pressure**—not textbook summaries.\n"
        "Each question must differ in **primary competency** tested (no overlapping scenarios).\n"
        "Do **not** include your private reasoning in the output."
    )


def cot_reasoning_scaffold_system_text() -> str:
    """
    Internal reasoning checklist for chain-of-thought (system prompt only).

    The model must follow this privately; visible output remains questions only.
    """
    return (
        "Before writing anything the candidate will see, reason **silently** through ALL of the following "
        "(do not output this analysis):\n"
        "1) **Role lens:** From the role title, category, seniority, and job description, what are the core "
        "responsibilities and measurable outcomes?\n"
        "2) **Strong vs weak signal:** What distinguishes a weak answer from a strong one at this seniority for "
        "this interview focus?\n"
        "3) **Revealing topics:** Which 3–6 topics are most discriminating for this round and focus (e.g. scale, "
        "reliability, data correctness, security, stakeholder alignment, delivery risk)?\n"
        "4) **Real-world friction:** What failure modes, incidents, ambiguity, or upstream changes would this role "
        "actually face?\n"
        "5) **Trade-offs:** Which design / process trade-offs should a great candidate articulate?\n"
        "6) **Question plan:** Map each output question to a different angle (concept vs scenario vs architecture vs "
        "debugging vs operational quality vs prioritization).\n"
        "Then write **only** the final numbered questions. Never reveal steps, headings, scratch work, or rationale."
    )
