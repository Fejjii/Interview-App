<!--
name: few_shot
description: Includes example questions to set style and depth.
-->

You are helping a candidate prepare for an interview in a realistic hiring context.

Use the following examples as a style guide (do not repeat them verbatim):

Example 1:
Role category: Software Engineering
Role/Title: Backend Engineer
Round: Technical Interview
Focus: Technical Knowledge
Questions:
1) Describe the trade-offs between REST and gRPC for internal services.
2) How would you design idempotent APIs for payment processing?

Example 2:
Role category: Data Analysis
Role/Title: Data Analyst
Round: Hiring Manager Interview
Focus: CV / Experience Deep Dive
Questions:
1) Walk me through a time you influenced a decision with data.
2) How do you validate data quality before reporting?

Now generate {n_questions} new questions for:
**Role category:** {role_category}
**Role/Title:** {role_title}
**Seniority:** {seniority}
**Interview round:** {interview_round}
**Interview focus:** {interview_focus}
**Difficulty:** {difficulty}
**Persona:** {persona}

Job description (optional):
{job_description}

Output as a numbered list only.
