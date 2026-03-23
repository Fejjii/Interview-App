<!--
name: chain_of_thought
description: Scenario for CoT-backed generation; reasoning steps live in the system prompt.
-->

Generate interview questions for this scenario. Apply the chain-of-thought technique **internally** (see system instructions)—your reply must contain **only** the questions.

**Role category:** {role_category}
**Target role title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Question difficulty:** {difficulty}
**Interviewer persona:** {persona}

Job description (optional):
{job_description}

Produce **{n_questions}** interview questions.

Output format:
- Numbered list **only** (1., 2., …). No preamble, no reasoning, no headings except the numbers.
