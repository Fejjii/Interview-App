# AI Interview Preparation Assistant

A **Streamlit** web app that helps candidates practice technical and behavioral interviews. It combines **OpenAI** language models with configurable prompts, a mock interview chat, question generation, answer feedback, and **CV-based interview prep**—all behind a layered **security and guardrail** pipeline suitable for portfolio and local production use.

**Workspace:** The main area uses **tabs** to switch between **Mock Interview**, **Interview Questions**, **CV Interview Prep**, and **Feedback / Evaluation**. The **Current Setup** strip summarizes your sidebar choices (including active **prompt strategy**).

---

## Features

| Area | What it does |
|------|----------------|
| **Sidebar configuration** | Role category, seniority, job description, interview round, focus, interviewer persona, **prompt strategy**, response language, and generation settings (model preset, temperature, top-p, max tokens). Shortcuts for generating questions, opening the mock interview, resetting the transcript, and managing saved sessions. |
| **Deployment (sidebar)** | Collapsible guidance and links for hosting the app (e.g. Streamlit Community Cloud, Azure, AWS, GCP, Docker). See also **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for container and cloud notes. |
| **Mock interview** | Turn-by-turn coaching: greetings, explicit “start interview” flows, generated questions, answer evaluation with follow-ups. |
| **Interview questions** | Structured questions from your current setup, optional **Compare Prompt Strategies**, optional debug prompts. |
| **Answer feedback** | Score-style feedback with strengths, gaps, and suggestions. |
| **CV interview prep** | Upload PDF/DOCX, structured extraction, tailored questions and practice modes. |
| **Dark mode** | Sidebar toggle; theme uses CSS tokens for readable contrast. |
| **Saved sessions** | Local JSON under `data/sessions/` (gitignored); list, open, delete. |
| **Guardrails** | Input validation, length limits, secret redaction, prompt-injection heuristics, moderation, rate limiting, and output checks (see [Security overview](#security--guardrails-overview)). |

---

## Architecture overview

The app follows a **thin UI → services → LLM** flow:

1. **Entry:** `streamlit_app.py` adds `src/` to `sys.path`, loads `.env`, calls `interview_app.app.main.run()`.
2. **App layer:** `app/main.py` composes theme, sidebar (`controls.py`), and main workspace (`layout.py`).
3. **Services:** `interview_generator`, `answer_evaluator`, `chat_service`, `cv_interview_service` implement domain flows; each runs inputs through `security/pipeline.py` before calling `llm/openai_client.py`.
4. **Prompts:** Templates and strategies live under `prompts/`; personas under `prompts/personas.py`.
5. **Persistence:** `storage/sessions.py` reads/writes session JSON.

For diagrams and module boundaries, see **[docs/architecture.md](docs/architecture.md)**.

---

## Prompt Strategies

The app ships with **five** composable prompting techniques for **interview question generation** (templates under `src/interview_app/prompts/templates/`). You pick one in the sidebar under **Prompt Strategy**:

| Strategy | What it does |
|----------|----------------|
| **Zero-shot** | Direct instructions only—no examples in the user prompt. |
| **Few-shot** | Includes example questions so the model matches style and depth. |
| **Chain-of-thought** | Asks the model to reason step-by-step internally (final output stays interview questions). |
| **Structured Output** | Requests machine-readable JSON matching a schema (good for strict parsing). |
| **Role-based** | Emphasizes a consistent interviewer persona together with your chosen persona tone. |

The **Current Setup** strip at the top of the workspace shows the active strategy (e.g. `Prompt · Few-shot`). The **Interview Questions** tab also shows **Active prompt strategy** above the controls.

### Strategy comparison

On the **Interview Questions** tab, **Compare Prompt Strategies** runs the same sidebar configuration **three** times—**zero-shot**, **few-shot**, and **chain-of-thought**—generating **one** question per strategy. Results appear in **three bordered columns** so you can compare wording and format. (Structured Output and Role-based are selectable for normal generation but are not included in this quick comparison to limit API calls.)

**Note:** Answer feedback and the CV prep pipeline use their own fixed system prompts; only the job-description-based question generator and mock-interview **question** turns follow the selected strategy.

---

## Tech stack

- **Python 3.11+**
- **Streamlit** — UI and session state
- **OpenAI Python SDK (v1+)** — chat completions
- **Pydantic / pydantic-settings** — configuration and structured models
- **langdetect** — optional language hints
- **pypdf, python-docx** — CV text extraction

Development tooling: **pytest**, **ruff**, **black**, **mypy** (see [docs/development.md](docs/development.md)).

---

## Installation and setup

### 1. Clone and virtual environment (Windows PowerShell example)

```powershell
cd path\to\sfejji-AE.1.5
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment variables

Copy the template and add your API key:

```powershell
copy .env.example .env
```

Edit `.env` (never commit it). See **[Environment variables](#environment-variables)** below.

---

## Environment variables

| Variable | Purpose | Notes |
|----------|---------|--------|
| `OPENAI_API_KEY` | OpenAI API access | **Required** for live LLM calls |
| `OPENAI_MODEL` | Default model name or preset key | Default: `gpt-4o-mini` |
| `OPENAI_TEMPERATURE` | Default sampling temperature | Default: `0.2` |
| `APP_ENV` | Logical environment label | e.g. `dev`, `prod` |
| `SESSIONS_DIR` | Where session JSON files are stored | Default: `data/sessions` (relative to process CWD) |

Security-related variables use the `SECURITY_` prefix (see [docs/security.md](docs/security.md)):

- `SECURITY_MAX_INPUT_LENGTH`, `SECURITY_OUTPUT_MAX_LENGTH`
- `SECURITY_RATE_LIMIT_MAX_REQUESTS`, `SECURITY_RATE_LIMIT_WINDOW_SECONDS`
- `SECURITY_MODERATION_ENABLED`, `SECURITY_PROMPT_INJECTION_STRICT`
- `SECURITY_CV_MAX_FILE_BYTES`, `SECURITY_CV_MAX_TEXT_CHARS`

---

## How to run the app

From the project root (repository folder containing `streamlit_app.py`):

```powershell
python -m streamlit run streamlit_app.py
```

(`streamlit run …` also works if `streamlit` is on your `PATH`.) Open the URL shown (typically `http://localhost:8501`).

---

## How to run tests

```powershell
pytest
pytest tests\unit -v
```

Integration tests under `tests/integration/` may be skipped unless `OPENAI_API_KEY` is set. Full detail: **[docs/testing.md](docs/testing.md)**.

---

## Project structure

```
sfejji-AE.1.5/
├── streamlit_app.py          # Entrypoint: path, .env, main.run()
├── pyproject.toml            # Project metadata and tool config
├── requirements.txt
├── .env.example              # Documented env vars (no secrets)
├── data/sessions/            # Saved sessions (gitignored)
├── docs/
│   ├── architecture.md
│   ├── development.md
│   ├── testing.md
│   ├── security.md
│   ├── DEPLOYMENT.md
│   └── PROJECT_OVERVIEW.md   # Longer narrative / diagrams
├── scripts/                  # Optional demos and smoke tests
├── src/interview_app/
│   ├── app/                  # Streamlit composition, layout, session state
│   ├── ui/                   # Theme, widgets, display helpers
│   ├── services/             # Interview, chat, CV pipelines
│   ├── prompts/              # Strategies, templates, personas
│   ├── llm/                  # OpenAI client, model presets
│   ├── security/             # Guards, pipeline, moderation, rate limits
│   ├── config/               # Settings from env
│   ├── storage/              # Session JSON I/O
│   ├── cv/                   # CV parsing, models, prompt builders
│   └── utils/                # Types, errors, language helpers
└── tests/
    ├── unit/
    └── integration/
```

---

## Security / guardrails overview

User and file-derived text is validated through a **single pipeline** (`security/pipeline.py`): length checks, sanitization, secret redaction, prompt-injection heuristics, optional moderation, and per-session rate limiting before the LLM; outputs are validated afterward. This is **defense in depth** for a client-trusted UI—not a substitute for server-side enforcement in a multi-tenant product.

Details, configuration, and manual test ideas: **[docs/security.md](docs/security.md)**.

---

## Roadmap / future improvements

- Optional **server-side** API with auth and centralized rate limits for multi-user deployment.
- **Structured outputs** (JSON schema) more consistently across all LLM surfaces.
- **Evaluation** harness for prompt/version regression tests.
- **i18n** beyond language instructions in prompts.
- **Observability** exports (OpenTelemetry) for production monitoring.

---

## Additional documentation

| Doc | Content |
|-----|---------|
| [docs/architecture.md](docs/architecture.md) | Layers, data flow, module map |
| [docs/development.md](docs/development.md) | Conventions, linting, extending prompts |
| [docs/testing.md](docs/testing.md) | Pytest, manual guardrail checks |
| [docs/security.md](docs/security.md) | Guardrails, env vars, operational notes |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker and cloud notes |

---

## License / author

See `pyproject.toml` for project metadata. Use `.gitignore` to keep `.env` and local session data out of version control.
