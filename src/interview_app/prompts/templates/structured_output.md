<!--
name: structured_output
description: JSON schema for questions with skill, difficulty, and rationale fields.
-->

Return **one JSON object** that matches this schema **exactly** (keys and nesting as shown). Fill the array with **{n_questions}** objects.

{{
  "questions": [
    {{
      "question": "string",
      "skill_tested": "string",
      "difficulty": "string",
      "why_it_matters": "string"
    }}
  ]
}}

**Field rules:**
- `question`: the full interview prompt as asked by an interviewer.
- `skill_tested`: short label (e.g., "API design", "stakeholder communication").
- `difficulty`: one of Easy | Medium | Hard | Expert (aligned to `{difficulty}` and seniority).
- `why_it_matters`: one sentence on what this question reveals about fit.

**Context inputs:**
- role_category: {role_category}
- role_title: {role_title}
- seniority: {seniority}
- interview_round: {interview_round}
- interview_focus: {interview_focus}
- calibration_difficulty: {difficulty}
- persona: {persona}
- job_description: {job_description}

**Output rules:**
- Valid JSON only. No markdown code fences. No text before or after the JSON object.
