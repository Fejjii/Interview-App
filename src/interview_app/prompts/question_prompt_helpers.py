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


def seniority_calibration_for_questions(*, seniority: str, role_category: str) -> str:
    """
    Explicit interview-depth instructions from candidate seniority.

    This block is injected into every question-generation user prompt so Junior
    vs Senior outputs diverge strongly (definitions vs architecture/trade-offs).
    """
    band = seniority_band(seniority)
    rc = (role_category or "").strip()

    if band == "junior":
        return (
            "**Seniority calibration (Entry-Level / Junior):** Focus on **foundational** knowledge.\n"
            "Prioritize: clear **definitions**, core concepts, **basic** ETL or pipeline steps, **basic SQL** and "
            "data modeling, **simple** data-quality checks, familiarity with common tools, and **short** realistic "
            "examples with limited moving parts.\n"
            "Avoid multi-service architecture essays, organization-wide governance, or principal-level platform "
            "design unless the interview focus explicitly requires a light touch of those topics."
        )

    if band == "mid":
        return (
            "**Seniority calibration (Mid-Level):** Balance **solid fundamentals** with **practical** experience.\n"
            "Include some scenario-based prompts and occasional **light** trade-offs, but do **not** make every "
            "question a large-scale system design or cost/ops deep dive. Escalate depth only when justified by "
            "the role title, category, and focus.\n"
            "Keep at least part of the set accessible without assuming the candidate owns org-wide platforms."
        )

    if band == "senior":
        parts = [
            "**Seniority calibration (Senior):** Prioritize **system thinking** and **decision-making** over "
            "glossary checks.\n"
            "Emphasize where appropriate: **system design** and architecture choices, explicit **trade-offs**, "
            "**scalability** and **performance** tuning under growth, **cost optimization** (e.g. warehouse or query "
            "efficiency), **reliability** and fault tolerance, **data quality frameworks**, **schema evolution** in "
            "production without breaking downstream consumers, **backfills** alongside SLAs, **orchestration** strategy, "
            "**observability** (monitoring and alerting for pipelines and data products), debugging **production** "
            "issues, **ambiguous requirements**, and leadership signals (reviews, mentoring, driving technical "
            "decisions).\n"
            "**Avoid** bare **definition-only** questions—if you ask what something *is*, fold it into a scenario "
            "that forces **prioritization**, **design**, or **debugging** reasoning.",
        ]
        if rc == "Data Engineering":
            parts.append(
                "**Style cues (Senior Data Engineer):** Aim for questions comparable to: designing **high-volume** "
                "pipelines with **quality + fault tolerance**; **schema changes** that must not break dashboards; "
                "**ETL runtime doubling**—how to diagnose and optimize; **real-time + batch** reporting from shared "
                "events; reducing **Snowflake/BigQuery** (or similar) **cost** at scale; **idempotent** loads; "
                "**monitoring/alerting** for **data quality** regressions."
            )
        return "\n".join(parts)

    # staff_plus — strictly deeper than Senior where relevant
    parts = [
        "**Seniority calibration (Lead / Staff / Principal / Architect-level):** Treat the candidate as someone who "
        "**owns or co-owns platforms**, sets **technical direction**, and operates under **organizational** "
        "constraints.\n"
        "Stress: cross-team **platform design**, standards and **governance** without killing velocity, "
        "multi-year **scalability** and **cost** strategy, **reliability engineering** for data products, advanced "
        "**data quality** and contract enforcement, **incident** command patterns, **ambiguous** executive asks, "
        "**mentoring** and raising the bar on reviews, and **prioritization** across competing roadmaps.\n"
        "Questions should feel **discriminating at the top of the band**—weak candidates hide behind buzzwords; "
        "strong candidates cite **metrics**, **failure modes**, and **explicit trade-offs**.\n"
        "**Avoid** Entry-Level-style definition drills unless used briefly to tee up a harder follow-on.",
    ]
    if rc == "Data Engineering":
        parts.append(
            "**Style cues (Senior+ Data Engineer):** Include org-scale concerns—e.g. **cost/perf** programs across "
            "many teams, **evolving contracts** for many consumers, **disaster** and **backfill** strategy at scale, "
            "**self-serve** vs **governed** data tensions."
        )
    return "\n".join(parts)


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
        "The **Seniority calibration** section above is authoritative: if it conflicts with generic difficulty "
        "hints, follow **Seniority calibration**.\n"
        "For Junior, several **definition or basic-steps** items are appropriate; for Senior/Staff, favor **depth** "
        "and **distinct angles** (do not repeat the same theme in different words)."
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
        "Honor **Seniority calibration** first: Junior exemplars may look “senior”; your **new** questions must still "
        "match the **candidate’s** seniority, not the exemplar difficulty.\n"
        "Vary across items: behavioral signals, technical depth, debugging/investigation, and prioritization—"
        "as appropriate to the interview focus.\n"
        "No duplicate themes; avoid generic filler (“Tell me about yourself”). For Senior/Staff, avoid **definition-only** "
        "items unless anchored in a deeper scenario (per calibration)."
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
        "Each question must differ in **primary competency** tested (no overlapping scenarios).\nMust align with the "
        "**Seniority calibration** block in the user message.\n"
        "Do **not** include your private reasoning in the output."
    )


def cot_reasoning_scaffold_system_text(seniority: str = "") -> str:
    """
    Internal reasoning checklist for chain-of-thought (system prompt only).

    The model must follow this privately; visible output remains questions only.
    """
    core = (
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
    band = seniority_band(seniority)
    if band == "junior":
        tail = (
            "\n\n**Junior (internal):** Keep internal hypotheses **small**—basic reasoning, core skills, simple "
            "scenarios. Do **not** force multi-service platform essays."
        )
    elif band == "mid":
        tail = (
            "\n\n**Mid (internal):** Mix fundamentals with **bounded** production context; occasional trade-off. "
            "Do **not** elevate every line to staff-level platform strategy."
        )
    else:
        tail = (
            "\n\n**Senior / Staff (internal):** Push **discriminating** depth—architecture, cost, reliability, data "
            "correctness under change, operational metrics, and leadership judgment. Weak answers stay generic or "
            "definition-heavy; strong answers cite **options**, **metrics**, and **failure modes**."
        )
    return core + tail
