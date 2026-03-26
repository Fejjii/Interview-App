<!--
name: few_shot
description: Domain- and focus-aligned exemplar questions, then a separate generation task.
Insert {seniority_calibration_block}: ties exemplar *style* to candidate band (Junior vs Senior).
-->

## Exemplars (few-shot — pattern only)

{few_shot_demonstrations}

---

## Your task (new questions)

You are simulating a **strong hiring conversation**. After the exemplars above, write **{n_questions}** **new** questions for the candidate below.

Requirements:
- Match exemplar **realism**: concrete situations, stakes, and interviewer-like wording.
- Stay aligned with **role title**, **focus**, **round**, **seniority**, and the job description.
- **Do not** copy or trivially paraphrase the exemplars; invent **fresh** scenarios.

**Role category:** {role_category}
**Target role title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Question difficulty:** {difficulty}
**Interviewer persona:** {persona}

{seniority_calibration_block}

{diversity_and_quality_block}

Job description (optional):
{job_description}

Output format:
- Numbered list **only** (`1.`, `2.`, …).
