<!--
name: structured_output
description: Produces JSON output for easier parsing in the UI.
-->

You are helping a candidate prepare for a professional interview.

Return a JSON object that matches this schema exactly:

{{
  "role_category": "string",
  "role_title": "string",
  "seniority": "string",
  "interview_round": "string",
  "interview_focus": "string",
  "questions": [
    {{
      "id": "q1",
      "question": "string",
      "tags": ["string"]
    }}
  ]
}}

Inputs:
- role_category: {role_category}
- role_title: {role_title}
- seniority: {seniority}
- interview_round: {interview_round}
- interview_focus: {interview_focus}
- difficulty: {difficulty}
- persona: {persona}
- job_description: {job_description}

Requirements:
- Generate {n_questions} items in "questions".
- "id" must be unique and stable (q1, q2, ...).
- Keep tags short (e.g., "behavioral", "system-design", "stakeholders", "metrics").
- Output JSON only. No markdown fences.
