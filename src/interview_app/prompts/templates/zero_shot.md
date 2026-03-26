<!--
name: zero_shot
description: Direct baseline interview questions—no examples, no reasoning scaffold in the reply.
-->

You are preparing for an interview. Generate **standard, direct** questions only—no worked examples in your reply and no “first I will think step-by-step” text.

**Role category:** {role_category}
**Target role title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Question difficulty:** {difficulty}
**Interviewer persona (tone hint only):** {persona}

{diversity_and_quality_block}

Job description (optional; ground in this text when helpful—do not invent employer-specific facts):
{job_description}

Produce exactly **{n_questions}** interview questions.

Output format:
- Numbered list **only** (`1.`, `2.`, …). One primary question per item.
- **Classic interview phrasing** (clear ask, moderate depth). Avoid elaborate multi-paragraph case studies.
