<!--
name: structured_output
description: Produces JSON output for easier parsing in the UI.
-->

You are helping a candidate prepare for a {interview_type} interview.

Return a JSON object that matches this schema exactly:

{{
  "role_title": "string",
  "seniority": "string",
  "interview_type": "string",
  "questions": [
    {{
      "id": "q1",
      "question": "string",
      "tags": ["string"]
    }}
  ]
}}

Inputs:
- role_title: {role_title}
- seniority: {seniority}
- interview_type: {interview_type}
- job_description: {job_description}

Requirements:
- Generate {n_questions} items in "questions".
- "id" must be unique and stable (q1, q2, ...).
- Keep tags short (e.g., "apis", "systems", "behavioral", "sql").
- Output JSON only. No markdown fences.
