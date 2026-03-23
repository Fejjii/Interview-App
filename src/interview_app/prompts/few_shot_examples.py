"""Curated few-shot demonstration questions keyed by interview focus.

Used only by ``build_few_shot_prompt`` so few-shot is demonstrably example-driven,
not a relabeled zero-shot prompt.
"""

from __future__ import annotations

from interview_app.app.interview_form_config import INTERVIEW_FOCUS_OPTIONS

# Three realistic questions per focus (behavior and depth match typical interviews).
_FOCUS_EXAMPLES: dict[str, tuple[str, str, str]] = {
    "Behavioral / Soft Skills": (
        "Tell me about a time you missed a deadline or underestimated effort. What did you change afterward?",
        "Describe a disagreement with a peer or manager where you did not get your way. How did you move forward?",
        "Give an example of giving difficult feedback. What was the situation, and what was the outcome?",
    ),
    "Technical Knowledge": (
        "How would you explain idempotency—and why it matters for external integrations—to a non-expert stakeholder in two minutes?",
        "Walk me through how you would debug a production issue that only affects a subset of users.",
        "What trade-offs would you weigh between reliability, cost, and speed for a change touching a critical path?",
    ),
    "Coding / Practical Exercise": (
        "How would you approach writing tests for a module that has been flaky in CI—what do you check first?",
        "Describe how you would refactor a hot path without changing external behavior.",
        "If you had 45 minutes to implement a minimal solution, how would you scope requirements and validate correctness?",
    ),
    "System Design / Architecture": (
        "How would you design an end-to-end flow for event-driven updates with clear ownership, retries, and failure handling?",
        "What interfaces or contracts would you define between services, and how would you version them safely?",
        "How would you reason about consistency versus availability for this workload, and what would you monitor in production?",
    ),
    "Leadership / Management": (
        "How do you prioritize when two senior stakeholders want opposite things and the timeline is fixed?",
        "Tell me how you have developed someone on your team who was underperforming.",
        "How do you measure whether your team is healthy, beyond velocity or output metrics?",
    ),
    "Culture Fit / Values": (
        "What kind of environment helps you do your best work, and how do you adapt when the culture is ambiguous?",
        "Describe a time you raised an ethical or safety concern. What was your process?",
        "How do you build trust with a new cross-functional team under delivery pressure?",
    ),
    "CV / Experience Deep Dive": (
        "Pick the project on your resume you are proudest of—what was your exact role versus the team’s?",
        "What was the hardest technical or organizational obstacle on that project, and how did you overcome it?",
        "If we spoke to a teammate from that project, what would they say you contributed uniquely?",
    ),
    "Business Case / Strategy": (
        "How would you structure an answer to a market-sizing or profitability question in this domain?",
        "What hypotheses would you test first if revenue growth stalled but usage looked healthy?",
        "How do you communicate a recommendation when the data is incomplete but a decision is due?",
    ),
    "Stakeholder Management": (
        "Tell me about a time requirements shifted late in a cycle. How did you reset expectations?",
        "How do you handle a stakeholder who wants a date you believe is unrealistic?",
        "Describe how you communicate risk upward without sounding like you are blocking progress.",
    ),
    "Salary / Negotiation Preparation": (
        "How would you articulate your compensation expectations when the range is unclear?",
        "What non-salary factors would you rank, and how would you trade them off?",
        "How do you respond to an initial offer that is below your expectations—walk me through your approach.",
    ),
}


def _normalize_focus(interview_focus: str) -> str:
    f = (interview_focus or "").strip()
    if f in _FOCUS_EXAMPLES:
        return f
    # Safe fallback: first catalog option
    return INTERVIEW_FOCUS_OPTIONS[0]


def build_few_shot_demonstration_block(
    *,
    role_category: str,
    role_title: str,
    seniority: str,
    interview_round: str,
    interview_focus: str,
) -> str:
    """
    Build a few-shot block: scenario line plus exactly three example questions.

    Questions are chosen for the selected **interview_focus**; the scenario line
    anchors the user's role category, title, seniority, and round so the model
    sees a coherent pattern before generating new questions.
    """
    focus_key = _normalize_focus(interview_focus)
    q1, q2, q3 = _FOCUS_EXAMPLES[focus_key]

    scenario = (
        f"**Demonstration scenario (style reference only — do not copy verbatim):**  \n"
        f"Role category: {role_category}  \n"
        f"Role/title: {role_title}  \n"
        f"Seniority: {seniority}  \n"
        f"Round: {interview_round}  \n"
        f"Focus: {focus_key}  \n"
    )

    questions = (
        "**Example questions that match this focus and depth:**\n\n"
        f"1. {q1}\n"
        f"2. {q2}\n"
        f"3. {q3}\n"
    )

    return f"{scenario}\n{questions}"
