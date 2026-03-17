<!--
name: chain_of_thought
description: Encourages step-by-step reasoning while keeping output concise.
-->

You are helping a candidate prepare for a {interview_type} interview.

Role/Title: {role_title}
Seniority: {seniority}

Job description (optional):
{job_description}

Task:
Generate {n_questions} interview questions.

Reasoning requirement:
- Think step-by-step to ensure good coverage and appropriate difficulty.
- Do NOT reveal your step-by-step reasoning in the final answer.

Output:
- Return only a numbered list of questions.
