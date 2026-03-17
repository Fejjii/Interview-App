# Development

## Environment

- Python **3.11+**
- Recommended: create a virtual environment (`.venv`) in the repo root.

## Common commands

### Install

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```bash
streamlit run streamlit_app.py
```

### Tests

```bash
pytest
```

### Lint / format / typecheck

```bash
ruff check src tests
black src tests
mypy src
```

## Project conventions

- **`src/` layout**: application code lives under `src/interview_app/`.
- **Small modules**: keep UI, services, prompts, and LLM wiring separated.
- **No secrets in git**: use `.env` locally; `.env.example` documents keys.

## Adding a new prompt strategy

1. Add or update a template in `src/interview_app/prompts/templates/` (optional).
2. Add a builder function in `src/interview_app/prompts/prompt_strategies.py` that returns a `PromptBuildResult` (system + user prompt).
3. Wire the new strategy into the UI control that selects strategies (`src/interview_app/app/controls.py`) and into the service function that uses it.
4. Add a unit test to validate the strategy’s prompt composition (recommended).

