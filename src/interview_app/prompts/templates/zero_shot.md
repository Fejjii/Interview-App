<!--
name: zero_shot
description: Direct instruction to generate interview questions.
-->

You are helping a candidate prepare for a realistic interview aligned with a professional hiring process.

**Role category:** {role_category}
**Target role title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Question difficulty:** {difficulty}
**Interviewer persona:** {persona}

Generate {n_questions} interview questions tailored to this scenario.

Job description (optional; use only what is provided—do not invent employer details):
{job_description}

Guidelines:
- Match the round and focus (e.g., recruiter screen vs technical vs system design).
- Calibrate depth to seniority and difficulty.
- Keep questions realistic for the role category and industry norms.
- Avoid trivia unless the focus explicitly calls for it.
- Output as a numbered list only.
