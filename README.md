# Interview Practice App (Streamlit + OpenAI)

Practice interviews by generating questions and evaluating answers with an LLM, wrapped in a small Streamlit UI.

- **What you do**: pick interview type + prompt strategy + model settings → generate questions or evaluate an answer.
- **What you can learn**: prompt engineering techniques, basic guardrails, and how to wire Streamlit → services → OpenAI cleanly.

If you want a longer narrative + diagrams, see `docs/PROJECT_OVERVIEW.md`.

## Quick start (Windows PowerShell)

Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure credentials (recommended):

- Copy `.env.example` → `.env`
- Set `OPENAI_API_KEY` inside `.env` (never commit `.env`)

Run the app:

```bash
streamlit run streamlit_app.py
```

## High-level architecture (how files connect)

Runtime flow (one request):

1. **Entry**: `streamlit_app.py` starts Streamlit, adds `src/` to the import path, loads `.env`, then calls `interview_app.app.main.run()`.
2. **UI**: `src/interview_app/app/main.py` builds the page and calls:
   - `src/interview_app/app/controls.py` to render the sidebar and return a `UISettings` snapshot.
   - `src/interview_app/app/layout.py` to render tabs and handle button clicks.
3. **Services (domain logic)**: button clicks call:
   - `src/interview_app/services/interview_generator.py::generate_questions`
   - `src/interview_app/services/answer_evaluator.py::evaluate_answer`
4. **Security + prompts + LLM** (inside services):
   - guardrails: `src/interview_app/security/guards.py`
   - prompt strategies/templates: `src/interview_app/prompts/prompt_strategies.py` + `src/interview_app/prompts/prompt_templates.py` + `src/interview_app/prompts/templates/*.md`
   - OpenAI call: `src/interview_app/llm/openai_client.py::LLMClient` (with presets from `src/interview_app/llm/model_settings.py`)
5. **Display**: results and debug info are rendered via `src/interview_app/ui/display.py` and inputs come from `src/interview_app/ui/widgets.py`.

## Prompt strategies (5 techniques)

Selectable in the sidebar (`Prompt strategy`):

- `zero_shot`
- `few_shot`
- `chain_of_thought` (asks the model to reason internally, but not reveal hidden reasoning)
- `structured_output` (asks for JSON)
- `role_based` (interviewer persona)

Turn on **Show debug** in the sidebar to see the exact **system + user prompts** for each run.

## Guardrails (what’s blocked / sanitized)

Before any OpenAI call, user inputs go through `src/interview_app/security/guards.py`:

- **Validation**: empty input and length limits
- **Sanitization**: basic secret redaction (best-effort)
- **Injection detection**: simple phrase/regex heuristics; blocks requests when suspected

## File map (what each file does)

### Root

- `streamlit_app.py`: Streamlit entrypoint; ensures `src/` imports work and loads `.env`, then calls `interview_app.app.main.run()`.
- `requirements.txt`: runtime + dev dependencies.
- `.env.example`: documented environment variables (copy to `.env` locally).
- `Makefile`: convenience commands (optional).
- `docs/`: deeper documentation (architecture, development notes, testing notes).
- `scripts/demo_proof.py`: small console demo to sanity-check templates + guardrails + prompt building.

### Application package (`src/interview_app/`)

- `app/main.py`: UI composition root (page config + header + sidebar + tabs).
- `app/controls.py`: sidebar widgets; returns `UISettings` (all user-selected knobs).
- `app/layout.py`: page layout + tab rendering; wires buttons to service calls.
- `services/interview_generator.py`: generates interview questions (guardrails → prompt strategy → LLM call).
- `services/answer_evaluator.py`: evaluates an answer (guardrails → evaluator prompt → LLM call).
- `prompts/prompt_templates.py`: loads `.md` templates from `prompts/templates/` safely.
- `prompts/prompt_strategies.py`: builds system/user prompts for each technique.
- `prompts/templates/*.md`: the actual prompt templates (human-editable).
- `security/guards.py`: guardrails (validate/sanitize/detect injection) + system prompt hardening helper.
- `llm/openai_client.py`: `LLMClient` wrapper around the OpenAI Python SDK; returns `LLMResponse`.
- `llm/model_settings.py`: model preset keys + default params used by the UI.
- `config/settings.py`: `Settings` loader (env + optional `.env`) + cached `get_settings()`.
- `ui/widgets.py`: reusable Streamlit input widgets (text areas).
- `ui/display.py`: reusable Streamlit display helpers (errors, responses, debug).
- `utils/types.py`: shared Pydantic models (`LLMResponse`, `LLMUsage`).

### Tests (`tests/`)

- `tests/conftest.py`: adds `src/` to `sys.path` for tests.
- `tests/unit/test_config.py`: settings defaults + env overrides.
- `tests/unit/test_guardrails.py`: guardrails behavior.
- `tests/unit/test_prompt_strategies.py`: prompt strategies return non-empty prompts.
- `tests/integration/test_openai_client_smoke.py`: optional OpenAI smoke test (skips without `OPENAI_API_KEY`).

## Tests

Run all tests:

```bash
pytest
```

Run only unit tests:

```bash
pytest tests/unit
```

Integration tests are safe by default and will skip unless `OPENAI_API_KEY` is set.

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

