# Interview Practice App (Streamlit + OpenAI)

Practice interviews by generating questions and evaluating answers with an LLM, wrapped in a small Streamlit UI.

See [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) for architecture, development story, and file reference.

## Reviewer notes (Sprint 1 rubric)

- **Model**: choose from `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-mini` in the sidebar.
- **5 prompting techniques**: `zero_shot`, `few_shot`, `chain_of_thought`, `structured_output`, `role_based`.
  - Turn on **Show debug** in the sidebar to see the **system + user prompts** used for each run.
- **Tunable settings**: temperature + max tokens are adjustable in the sidebar and are passed to the OpenAI call.
- **Security guard**: user inputs run through guardrails (length/empty checks + prompt injection heuristics + basic secret redaction). If suspected injection is detected, the request is blocked and shown in the UI.

## Requirements

- Python **3.11+**

## Setup (Windows PowerShell)

Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional: configure environment variables.

- Copy `.env.example` to `.env`
- Set `OPENAI_API_KEY` to enable real OpenAI calls

## Run the app

```bash
streamlit run streamlit_app.py
```

## What the app does

- **Question generation**: generate practice questions based on interview type, role, seniority, and optional job description.
- **Answer feedback**: paste a question and your answer to receive coaching-style evaluation.

## Tests

Run all tests:

```bash
pytest
```

Run only unit tests:

```bash
pytest tests/unit
```

Integration tests are written to be safe by default and will skip unless `OPENAI_API_KEY` is set.

## Lint / Format / Typecheck

```bash
ruff check src tests
black src tests
mypy src
```

## Makefile (optional)

If you have `make` available:

```bash
make install
make run
make test
make lint
make format
make typecheck
```

On Windows without `make`, the PowerShell equivalents are shown in the sections above.

