<!--
name: chain_of_thought
description: User scenario for senior, situational questions; private reasoning protocol is only in the system prompt.
-->

Follow the **chain-of-thought protocol in the system message** privately. Your visible answer must be **only** the questions—no analysis, headings, or “reasoning:” sections.

This mode targets **deeper, situational prompts** than baseline generation: trade-offs, scale, reliability, data correctness, incidents, prioritization, and design judgment—as appropriate to seniority and focus.

**Role category:** {role_category}
**Target role title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Question difficulty:** {difficulty}
**Interviewer persona:** {persona}

{diversity_and_quality_block}

Job description (optional; use for grounding realistic scenarios):
{job_description}

Produce exactly **{n_questions}** questions.

Output format:
- Numbered list **only** (`1.`, `2.`, …). No preamble.
