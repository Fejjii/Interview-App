<!--
name: zero_shot
description: Direct instruction to generate interview questions.
-->

You are helping a candidate prepare for a {interview_type} interview.

Generate {n_questions} interview questions tailored to the following target role.

Role/Title: {role_title}
Seniority: {seniority}

Job description (optional):
{job_description}

Guidelines:
- Keep questions realistic for the role and seniority.
- Mix conceptual and practical questions.
- Avoid trivia unless explicitly requested.
- Output as a numbered list only.
