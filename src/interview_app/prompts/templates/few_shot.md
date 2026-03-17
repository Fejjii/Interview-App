<!--
name: few_shot
description: Includes example questions to set style and depth.
-->

You are helping a candidate prepare for a {interview_type} interview.

Use the following examples as a style guide (do not repeat them verbatim):

Example 1:
Role/Title: Backend Engineer
Seniority: Mid
Questions:
1) Describe the trade-offs between REST and gRPC for internal services.
2) How would you design idempotent APIs for payment processing?

Example 2:
Role/Title: Data Analyst
Seniority: Junior
Questions:
1) How do you validate data quality in a reporting pipeline?
2) What is the difference between correlation and causation? Give an example.

Now generate {n_questions} new questions for:
Role/Title: {role_title}
Seniority: {seniority}

Job description (optional):
{job_description}

Output as a numbered list only.
