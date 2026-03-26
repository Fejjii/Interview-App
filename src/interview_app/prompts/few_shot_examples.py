"""Few-shot exemplars for interview question generation.

Examples are selected by **domain** (from role category), **interview focus**,
**seniority band**, and **round** so few-shot mode steers toward realistic,
scenario-based interviewer questions—not a lightly relabeled zero-shot prompt.
"""

from __future__ import annotations

from interview_app.app.interview_form_config import INTERVIEW_FOCUS_OPTIONS
from interview_app.prompts.question_prompt_helpers import seniority_band

# Role category → compact domain key used to pick exemplar pools.
_CATEGORY_TO_DOMAIN: dict[str, str] = {
    "Software Engineering": "swe",
    "Data Engineering": "data_eng",
    "Data Analysis": "data_analysis",
    "AI / Machine Learning": "ml",
    "Product Management": "pm",
    "Cloud / DevOps": "devops",
    "Cybersecurity": "security",
    "Business Analysis": "business_analysis",
    "Consulting": "consulting",
    "QA / Testing": "qa",
    "Design / UX": "design",
    "Finance": "finance",
    "Operations": "operations",
    "Other": "general",
    "Sales / Customer Success": "general",
    "HR / People Operations": "general",
    "Marketing": "general",
}

# Exactly four templates per pool; use ``{role_title}`` where the title should appear.
_DOMAIN_FOCUS_POOLS: dict[tuple[str, str], tuple[str, str, str, str]] = {
    # --- Data Engineering (user-requested style) ---
    ("data_eng", "Technical Knowledge"): (
        "How would you redesign a slow nightly ETL workflow that now misses its SLA as data volume grows—"
        "what would you change first, and how would you prove the fix?",
        "A key dashboard shows inconsistent numbers after an upstream schema change. How would you investigate "
        "end-to-end and stabilize reporting for stakeholders?",
        "How would you design a pipeline that supports both batch regulatory reporting and near-real-time "
        "operational analytics from the same event streams?",
        "As **{role_title}**, a critical job sometimes double-loads partitions after retries—how do you make "
        "loads **idempotent** and safe without slowing the whole pipeline?",
    ),
    ("data_eng", "System Design / Architecture"): (
        "Design how **{role_title}** would move a batch-only warehouse incrementally toward near-real-time "
        "anomaly detection: what components, what SLAs, and what failure modes do you plan for?",
        "How would you separate concerns between ingestion, transformation, and serving layers so teams can evolve "
        "schemas without breaking downstream consumers?",
        "You need backfills without blocking live traffic. Walk through your approach to isolation, resource control, "
        "and validation.",
        "Compare strategies for **exactly-once** vs **at-least-once** processing in your stack—when is each "
        "acceptable, and how do you detect and repair duplicates?",
    ),
    ("data_eng", "Coding / Practical Exercise"): (
        "Given messy arrival-time timestamps across zones, how would **{role_title}** normalize and validate them "
        "before aggregation—what tests would you add?",
        "A dbt model is correct on a sample but wrong in production. How do you bisect whether the bug is source, "
        "join logic, or incremental freshness?",
        "You must trim warehouse cost 30% without missing daily reports—what do you measure first and what do you cut?",
        "Write down how you’d implement a **slowly-changing dimension** strategy for a core entity—what trade-offs "
        "do you accept for query speed vs history fidelity?",
    ),
    ("data_eng", "Behavioral / Soft Skills"): (
        "Tell me about a time **{role_title}** work slipped because upstream specs were wrong—how did you reset "
        "expectations and still deliver something useful?",
        "Describe disagreeing with analytics or product on a metric definition that affected a launch decision.",
        "When a pipeline you owned broke during a holiday freeze, what was your communication and mitigation plan?",
        "Give an example of mentoring a junior engineer on data quality—what habit changed afterward?",
    ),
    # --- Software Engineering ---
    ("swe", "Technical Knowledge"): (
        "How would you explain **idempotency** and **at-least-once delivery** to a product peer—and give a concrete "
        "failure mode if you get it wrong in production?",
        "A bug hits only a small slice of users on one platform version. How does **{role_title}** narrow root cause "
        "and ship a safe fix?",
        "You must trade latency vs storage on a read-heavy path—what metrics and experiments guide the decision?",
        "Walk through rolling out a **breaking API change** when mobile clients update slowly—how do you phase it?",
    ),
    ("swe", "System Design / Architecture"): (
        "Sketch how **{role_title}** would design notification delivery at scale with idempotent sends and retries—"
        "what components and ownership boundaries?",
        "How do you evolve service contracts when three downstream teams depend on your events?",
        "A cache stampede appears under flash traffic. What architectural changes and safeguards do you consider?",
        "Compare sync HTTP vs event-driven updates for a core domain—when does each win, and what operational cost "
        "do you accept?",
    ),
    ("swe", "Coding / Practical Exercise"): (
        "A module is flaky only in CI—what do you inspect first, and how do you make failures reproducible?",
        "Refactor a hot path without behavior change: how do **{role_title}** lock in correctness?",
        "You have 45 minutes to ship a minimal feature—how do you cut scope and verify you didn’t break invariants?",
        "How do you test time-dependent or asynchronous logic without brittle sleeps?",
    ),
    # --- ML / AI ---
    ("ml", "Technical Knowledge"): (
        "A model’s offline metrics look great but production outcomes regress—how does **{role_title}** investigate?",
        "How would you detect and mitigate **data drift** for a classifier updated quarterly?",
        "When would you choose a simpler model over a heavier one in production—what’s your decision framework?",
        "Explain how you’d version datasets and tie them to model releases for auditability.",
    ),
    ("ml", "System Design / Architecture"): (
        "Design online inference for **{role_title}** with latency SLOs, fallbacks when the model host is unhealthy, "
        "and safe rollout of a new version.",
        "Batch training overlaps with streaming features—how do you prevent train/serve skew?",
        "How would you architect human-in-the-loop review when false positives are costly?",
        "Walk through cost controls when GPU spend spikes after a traffic milestone.",
    ),
    # --- DevOps / SRE ---
    ("devops", "Technical Knowledge"): (
        "During a regional outage, half of your alerts are noise—how does **{role_title}** stabilize observability "
        "before the next incident?",
        "Compare blue/green vs canary for a stateful service—what risks do you mitigate in each?",
        "A deployment speeds up releases but increases Sev2s—what guardrails do you add without killing velocity?",
        "How do you safely rotate secrets used by many microservices?",
    ),
    ("devops", "System Design / Architecture"): (
        "Design a multi-region active-passive story for **{role_title}**—RPO/RTO, failover drills, and data paths.",
        "How do you give developers self-service deploys without bypassing security and change policy?",
        "You inherit a cluster with no resource limits—what’s your first week’s hardening plan?",
        "Describe how you’d implement progressive delivery with automated rollback signals.",
    ),
    # --- Security ---
    ("security", "Technical Knowledge"): (
        "A dependency scanner flags a critical CVE with no patch yet—what’s **{role_title}**’s containment plan?",
        "How do you threat-model a new public API before launch?",
        "Walk through investigating possible credential stuffing vs a misconfiguration.",
        "Compare preventive controls vs detective controls for insider risk in SaaS tooling.",
    ),
    # --- Product Management ---
    ("pm", "Business Case / Strategy"): (
        "Usage is up but revenue flattening—what hypotheses does **{role_title}** test first and in what order?",
        "A exec asks for a date you don’t believe in—how do you reframe with evidence and options?",
        "How would you sequence discovery vs delivery when tech debt blocks a big bet?",
        "Compare growing ARPU vs growing activation for the next half—what would change your mind?",
    ),
    ("pm", "Stakeholder Management"): (
        "Engineering says a committed roadmap item is much harder mid-quarter—how does **{role_title}** navigate?",
        "Legal pushes back on a launch feature—how do you unblock without blowing the timeline?",
        "Two VPs want opposite priorities with one team—what process gets you to a decision?",
        "How do you say no to a powerful stakeholder while preserving the relationship?",
    ),
}

# Generic pools: any domain not listed above falls back to (general, focus).
_GENERIC_FOCUS_POOLS: dict[str, tuple[str, str, str, str]] = {
    "Behavioral / Soft Skills": (
        "Tell me about a time you missed a deadline or underestimated effort. What did you change afterward?",
        "Describe a disagreement with a peer or manager where you did not get your way. How did you move forward?",
        "Give an example of giving difficult feedback. What was the situation, and what was the outcome?",
        "When **{role_title}** work depended on another team that slipped, how did you communicate and recover?",
    ),
    "Technical Knowledge": (
        "How would you explain a core technical concept your stakeholders misunderstand—without jargon dumping?",
        "Walk me through debugging a production-leaning issue that only reproduces under some user conditions.",
        "What trade-offs would you weigh between reliability, cost, and speed for a change touching a critical path?",
        "How does **{role_title}** decide what to instrument before vs after a risky launch?",
    ),
    "Coding / Practical Exercise": (
        "How would you approach writing tests for a module that has been flaky in CI—what do you check first?",
        "Describe how you would refactor a hot path without changing external behavior.",
        "If you had 45 minutes to implement a minimal solution, how would you scope and validate correctness?",
        "How would you review a teammate’s PR that touches concurrency—what are you looking for?",
    ),
    "System Design / Architecture": (
        "How would you design an end-to-end flow for event-driven updates with clear ownership, retries, "
        "and failure handling?",
        "What interfaces or contracts would you define between services, and how would you version them safely?",
        "How would you reason about consistency versus availability for this workload, and what would you monitor?",
        "Where would **{role_title}** draw boundaries between synchronous workflows and async processing?",
    ),
    "Leadership / Management": (
        "How do you prioritize when two senior stakeholders want opposite things and the timeline is fixed?",
        "Tell me how you have developed someone on your team who was underperforming.",
        "How do you measure whether your team is healthy, beyond velocity or output metrics?",
        "Describe calibrating performance when the business context kept changing mid-cycle.",
    ),
    "Culture Fit / Values": (
        "What kind of environment helps you do your best work, and how do you adapt when the culture is ambiguous?",
        "Describe a time you raised an ethical or safety concern. What was your process?",
        "How do you build trust with a new cross-functional team under delivery pressure?",
        "Tell me about **{role_title}** work where you had to balance speed with quality—how did you decide?",
    ),
    "CV / Experience Deep Dive": (
        "Pick the project on your resume you are proudest of—what was your exact role versus the team’s?",
        "What was the hardest technical or organizational obstacle on that project, and how did you overcome it?",
        "If we spoke to a teammate from that project, what would they say you contributed uniquely?",
        "What would you do differently on that project with hindsight?",
    ),
    "Business Case / Strategy": (
        "How would you structure an answer to a market-sizing or profitability question in this domain?",
        "What hypotheses would you test first if revenue growth stalled but usage looked healthy?",
        "How do you communicate a recommendation when the data is incomplete but a decision is due?",
        "How does **{role_title}** stress-test a strategy against competitive and regulatory risk?",
    ),
    "Stakeholder Management": (
        "Tell me about a time requirements shifted late in a cycle. How did you reset expectations?",
        "How do you handle a stakeholder who wants a date you believe is unrealistic?",
        "Describe how you communicate risk upward without sounding like you are blocking progress.",
        "When two departments interpreted success differently, how did you align them?",
    ),
    "Salary / Negotiation Preparation": (
        "How would you articulate compensation expectations when the range is unclear?",
        "What non-salary factors would you rank, and how would you trade them off?",
        "How do you respond to an initial offer below expectations—walk through your approach.",
        "How do you handle **{role_title}** negotiations when you still want the role but need movement on terms?",
    ),
}


_ROUND_ROUND_ARCH_HEAVY: frozenset[str] = frozenset(
    {"System Design Interview", "Final Interview", "Executive Interview"}
)


def _domain_for_category(role_category: str) -> str:
    return _CATEGORY_TO_DOMAIN.get((role_category or "").strip(), "general")


def _normalize_focus(interview_focus: str) -> str:
    f = (interview_focus or "").strip()
    if f in _GENERIC_FOCUS_POOLS:
        return f
    return INTERVIEW_FOCUS_OPTIONS[0]


def _pool_for(domain: str, focus_key: str) -> tuple[str, str, str, str]:
    key = (domain, focus_key)
    if key in _DOMAIN_FOCUS_POOLS:
        return _DOMAIN_FOCUS_POOLS[key]
    return _GENERIC_FOCUS_POOLS[focus_key]


def _example_count_for_config(
    seniority: str,
    interview_round: str,
    interview_focus: str,
) -> int:
    """Return 2–4 exemplars: more for senior bands and architecture-heavy rounds."""
    band = seniority_band(seniority)
    rd = (interview_round or "").strip()
    focus_key = _normalize_focus(interview_focus)
    arch_focus = focus_key == "System Design / Architecture"

    if band == "junior":
        return 3
    if rd in _ROUND_ROUND_ARCH_HEAVY or arch_focus:
        return 4
    if band in {"senior", "staff_plus"}:
        return 4
    return 3


def _pick_ordered_examples(
    pool: tuple[str, str, str, str],
    interview_round: str,
    n_take: int,
) -> tuple[str, ...]:
    """Rotate emphasis slightly by round so system-design rounds see more architecture-heavy exemplars first."""
    a, b, c, d = pool
    rd = (interview_round or "").strip()
    if rd == "System Design Interview":
        ordered = (c, a, d, b)
    elif rd in ("Technical Interview", "Case Study Interview"):
        ordered = (a, b, d, c)
    elif rd == "Behavioral Interview":
        ordered = (b, a, c, d)
    else:
        ordered = (a, b, c, d)
    return ordered[: max(2, min(n_take, 4))]


def get_few_shot_examples(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
) -> tuple[str, ...]:
    """
    Return 2–4 formatted example strings for the few-shot block.

    Examples adapt to category, title, seniority band, round, and focus.
    """
    domain = _domain_for_category(role_category)
    focus_key = _normalize_focus(interview_focus)
    pool = _pool_for(domain, focus_key)
    n_take = _example_count_for_config(seniority, interview_round, interview_focus)
    chosen = _pick_ordered_examples(pool, interview_round, n_take)
    title = (role_title or "").strip() or "this hire"
    return tuple(s.format(role_title=title) for s in chosen)


def few_shot_trace_for_debug(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
) -> dict[str, str | int]:
    """Safe metadata for opt-in debug UI and tests (no full prompt text)."""
    domain = _domain_for_category(role_category)
    focus_key = _normalize_focus(interview_focus)
    examples = get_few_shot_examples(
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
    )
    return {
        "few_shot_domain": domain,
        "few_shot_focus_resolved": focus_key,
        "few_shot_example_count": len(examples),
    }


def build_few_shot_demonstration_block(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
) -> str:
    """
    Build the user-visible few-shot block: scenario metadata plus numbered examples.
    """
    domain = _domain_for_category(role_category)
    focus_key = _normalize_focus(interview_focus)
    examples = get_few_shot_examples(
        role_category=role_category,
        role_title=role_title,
        seniority=seniority,
        interview_round=interview_round,
        interview_focus=interview_focus,
    )

    scenario = (
        "**Demonstration context (style reference only — do not copy verbatim):**  \n"
        f"Role category: {role_category}  \n"
        f"Domain exemplar pack: {domain}  \n"
        f"Role/title: {role_title}  \n"
        f"Seniority: {seniority}  \n"
        f"Round: {interview_round}  \n"
        f"Focus: {focus_key}  \n"
    )

    lines = "\n".join(f"{i}. {q}" for i, q in enumerate(examples, start=1))
    questions = f"**Example interview questions (tone + realism targets):**\n\n{lines}\n"

    return f"{scenario}\n{questions}"
