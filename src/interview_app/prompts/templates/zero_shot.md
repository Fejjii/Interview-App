<!--
name: zero_shot
description: Direct instruction only—no examples, no explicit reasoning protocol in the reply.
-->

Generate interview preparation questions using **only** the scenario below. Do not include examples of your own, do not outline a reasoning plan, and do not add commentary—only the questions.

**Role category:** {role_category}
**Target role title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Question difficulty:** {difficulty}
**Interviewer persona (context for tone):** {persona}

Produce **{n_questions}** distinct interview questions tailored to this setup.

Job description (optional; use only what is provided—do not invent employer details):
{job_description}

Output format:
- Numbered list **only** (1., 2., …). One question per item.
