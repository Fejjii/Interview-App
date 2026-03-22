<!--
name: chain_of_thought
description: Encourages step-by-step reasoning while keeping output concise.
-->

You are helping a candidate prepare for a realistic interview aligned with a professional hiring process.

**Role category:** {role_category}
**Role/Title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Difficulty:** {difficulty}
**Persona:** {persona}

Job description (optional):
{job_description}

Task:
Generate {n_questions} interview questions.

Reasoning requirement:
- Think step-by-step to ensure good coverage and appropriate difficulty for the round and focus.
- Do NOT reveal your step-by-step reasoning in the final answer.

Output:
- Return only a numbered list of questions.
