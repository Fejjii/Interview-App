# Interview Practice App (Streamlit + OpenAI)

Practice interviews by simulating a mock chat, generating targeted questions, and evaluating answers with an LLM—wrapped in a Streamlit UI with sidebar configuration, optional dark mode, and security guardrails.

## Features

- **Sidebar configuration** — Role, seniority, job description, interview round, focus, interviewer persona, response language, and advanced options (difficulty mode, prompt strategy, model, temperature, top-p, max tokens). Shortcuts: generate questions, open mock interview, reset transcript, reopen saved sessions.
- **Mock interview chat** — Back-and-forth practice with the coach; session save/new; configuration summary bar on the main page.
- **Interview question generator** — Produces structured questions from your current setup (with optional debug prompts).
- **Answer evaluation** — Paste a question and answer for scored feedback (strengths, gaps, suggestions).
- **Dark mode** — Toggle in the sidebar; theme uses CSS tokens and Streamlit/Base Web overrides for readable contrast on inputs, dropdowns, labels, and chat.
- **Security guards** — Input validation, length limits, moderation/rate limiting, output checks, and injection heuristics via the security pipeline (see `src/interview_app/security/`).

If you want a longer narrative and diagrams, see `docs/PROJECT_OVERVIEW.md`.

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
   - `src/interview_app/app/controls.py` — `render_sidebar_configuration()` returns a `UISettings` snapshot.
   - `src/interview_app/app/layout.py` — hero, configuration pill bar, workspace (Mock Interview / Questions / Feedback), chat and service wiring.
   - `src/interview_app/ui/theme.py` — light/dark CSS and custom HTML styling.
3. **Services**: `interview_generator`, `answer_evaluator`, `chat_service` call the LLM after guardrails.
4. **Security + prompts + LLM**: `security/pipeline.py`, `guards.py`, prompts and templates, `llm/openai_client.py`.
5. **Display**: `ui/display.py`, `ui/widgets.py`. Sessions: `storage/sessions.py`.

## Prompt strategies (5 techniques)

Selectable under **Advanced settings** in the sidebar:

- `zero_shot`, `few_shot`, `chain_of_thought`, `structured_output`, `role_based`

Turn on **Show debug** to see system + user prompts when supported.

## Guardrails

User inputs are validated and passed through the security pipeline (`security/pipeline.py`) where configured: length limits, moderation, rate limiting, injection heuristics, and output guarding. See unit tests under `tests/unit/test_*.py` for guards, pipeline, and moderation.

## File map (selected)

| Path | Role |
|------|------|
| `streamlit_app.py` | Entrypoint; `sys.path` + `.env` + `main.run()` |
| `app/main.py` | Page config, theme, sidebar + main composition |
| `app/controls.py` | Sidebar UI → `UISettings` |
| `app/layout.py` | Main workspace, chat, questions tab, feedback tab |
| `app/ui_settings.py` | `UISettings` dataclass |
| `app/conversation_state.py` | Chat + session state helpers |
| `ui/theme.py` | Light/dark CSS |
| `services/chat_service.py` | Mock interview turns |
| `storage/sessions.py` | Saved session JSON |

## Tests

```bash
pytest
pytest tests/unit
```

Integration tests skip unless `OPENAI_API_KEY` is set.

## Lint / format / typecheck

```bash
ruff check src tests
black src tests
mypy src
```

## Deployment (Docker + cloud)

See `docs/DEPLOYMENT.md` for Docker and cloud notes.
