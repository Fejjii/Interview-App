# AI Interview Preparation Assistant

A **Streamlit** web app that helps candidates practice technical and behavioral interviews. It combines **OpenAI** language models with configurable prompts, a mock interview chat, question generation, answer feedback, and **CV-based interview prep**—all behind a layered **security and guardrail** pipeline suitable for portfolio and local production use.

**Workspace:** The main area uses **tabs** to switch between **Mock Interview**, **Interview Questions**, **CV Interview Prep**, and **Feedback / Evaluation**. The **Current Setup** strip summarizes your sidebar choices (including active **prompt strategy**).

---

## Features

| Area | What it does |
|------|----------------|
| **Sidebar configuration** | Role category, seniority, job description, interview round, focus, interviewer persona, **question difficulty** (Auto or fixed Easy / Medium / Hard), **prompt strategy**, response language, **model** (GPT-4.1 family, GPT-4o, GPT-4o mini), generation sliders (temperature, top-p, max tokens), optional **Show debug prompts**, shortcuts, and saved sessions. |
| **Deployment (sidebar)** | Collapsible guidance and links for hosting the app (e.g. Streamlit Community Cloud, Azure, AWS, GCP, Docker). See also **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for container and cloud notes. |
| **Mock interview** | Turn-by-turn coaching: greetings, explicit “start interview” flows, generated questions, answer evaluation with follow-ups. |
| **Interview questions** | Structured questions from your current setup, optional **Compare Prompt Strategies**, optional debug prompts. |
| **Answer feedback** | Score-style feedback with strengths, gaps, and suggestions. |
| **CV interview prep** | Upload PDF/DOCX, structured extraction, tailored questions and practice modes. |
| **Dark mode** | Sidebar toggle; theme uses CSS tokens for readable contrast. |
| **Saved sessions** | Local JSON under `data/sessions/` (gitignored), **scoped by usage mode** (Demo vs BYO); list, open, delete. |
| **Guardrails** | Input validation, length limits, secret redaction, prompt-injection heuristics, moderation, rate limiting, and output checks (see [Security overview](#security--guardrails-overview)). |

---

## Session setup: Demo mode vs Bring Your Own (BYO) API key

At the top of the sidebar, **Session setup** controls how API calls are billed for **this browser session** (Streamlit server-side `session_state` only):

| Mode | Billing | API key source |
|------|---------|----------------|
| **Demo mode** | Uses the **server** project key from `OPENAI_API_KEY` in `.env` / environment. | Not entered in the UI. |
| **Use your own OpenAI API key (BYO)** | Uses **your** key for this session. | Typed once per apply; stored only in memory for the active Streamlit session. |

**Behavior:**

- **Masked input:** In BYO mode, the key field defaults to **password** style; optional **Show key** reveals it locally.
- **Session-only:** BYO keys are **not** written to disk, `localStorage`, or saved session JSON. They exist only in server memory until the tab/session ends or you apply a different mode.
- **Full reset on Apply:** Clicking **Apply usage mode** runs a **full workspace reset**: mock interview transcript, CV prep state, strategy comparison, feedback fields, rate-limit counters, and in-memory BYO secrets are cleared, then the new mode (and BYO key if applicable) is applied. Sidebar preferences such as role, interview setup, and dark mode are **preserved**.
- **Confirmation:** If you have unsaved work (messages, loaded session, CV analysis, or a strategy comparison), you must check a confirmation box before Apply proceeds.
- **No cross-mode leakage:** Switching Demo ↔ BYO does not leave the previous mode’s chat or CV data in the UI; each Apply starts from a clean workspace for that mode.

If Demo mode is selected but the server has **no** `OPENAI_API_KEY`, the UI shows a warning—configure the environment or switch to BYO with your key.

---

## Saved sessions and isolation

Saved mock interviews are JSON files under `SESSIONS_DIR` (default `data/sessions/`). They are **isolated by usage scope**:

- **Demo mode** sees sessions under `demo/` plus **legacy** flat `*.json` files at the sessions root (treated as Demo history).
- **BYO mode** (with an applied key) sees only sessions under `byo/<sha256-of-key>/` for **that** key. Another BYO key gets a different folder. Demo sessions **do not** appear when you are in BYO mode, and vice versa.

Each saved file may include a `usage_scope` tag (e.g. `demo`, `byo:<hex>`) for clarity; the directory layout is authoritative for listing.

After switching modes with **Apply usage mode**, the sidebar session list reflects **only** the current scope (a rerun runs automatically).

---

## CV Interview Prep: Practice vs full prep

On **CV Interview Prep**, after uploading a CV and running analysis:

- **Practice (questions only):** Generates tailored **questions** without model “ideal” answers in that step. You type answers in the UI, then **Evaluate answers** runs structured feedback in batch (Pydantic-parsed).
- **Full prep:** Produces the **full bundle**—overview-style context, questions, model answers, and follow-ups in one generation pass—using structured JSON validated with **`cv/models.py`** (same guardrail and JSON parsing pipeline as extraction).

Both paths use the same extraction + guardrails; only the generation prompt and output model differ (`generation_mode` in `services/cv_interview_service.py`).

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

The app ships with **five** composable prompting techniques for **interview question generation**. Implementation details live in `src/interview_app/prompts/prompt_strategies.py`, templates in `src/interview_app/prompts/templates/`, and focus-aligned few-shot demonstrations in `src/interview_app/prompts/few_shot_examples.py`. You pick one in the sidebar under **Prompt Strategy**:

| Strategy | What it means in this app | What you should see |
|----------|---------------------------|---------------------|
| **Zero-shot** | User prompt is **direct instructions only** (numbered list). System prompt states the technique and **does not** inject persona calibration—persona appears only as one line of context in the user prompt. | Straight, standard questions with minimal prompting machinery. |
| **Few-shot** | **Three demonstration questions** are injected per **interview focus** (from `few_shot_examples.py`), plus a scenario line using your role, seniority, and round—then a separate “generate new questions” task. | Questions that follow the **pattern and depth** of the demonstrations without copying them. |
| **Chain-of-thought** | **Internal** reasoning steps (priorities, competencies, seniority/round fit, question plan) are specified in the **system** prompt; the user prompt is scenario + “numbered list only” so reasoning is not echoed. | Often more targeted, competency-aligned questions; output should still be **only** questions. |
| **Structured Output** | Model must return **valid JSON** with a `questions` array; each item has `question`, `skill_tested`, `difficulty`, `why_it_matters`. The Interview Questions tab renders these fields in expanders; invalid JSON falls back to a raw view with a warning. | Schema-shaped output with metadata per question. |
| **Role-based** | **Strong interviewer assignment** in the user prompt (`persona_identity` + full `persona_behavior` text from `personas.py`) and instructions to sound like a live interviewer. | Tone and framing driven by persona + role (vs. neutral zero-shot). |

The **Current Setup** strip at the top of the workspace shows the active strategy (e.g. `Prompt · Few-shot`). The **Interview Questions** tab also shows **Active prompt strategy** above the controls.

### Strategy comparison

On the **Interview Questions** tab, **Strategy Comparison** lets you pick **Strategy A** and **Strategy B** from the same five techniques, then **Compare Selected Strategies**. The app uses your current sidebar setup and **Number of questions** to generate both runs, then shows results **side by side** in aligned rows (Question 1 vs Question 1, etc.). Structured Output rows include optional captions for skill, difficulty, and “why it matters” when JSON parses cleanly. Below that, **Evaluate the strategies** offers sliders (realism, difficulty match, overall quality), a **Winner** choice, and **Save evaluation**—appended to `data/strategy_comparison_evaluations.json` for local review.

**Note:** Answer feedback and the CV prep pipeline use their own fixed system prompts; only the job-description-based question generator and mock-interview **question** turns follow the selected strategy. If **Structured Output** is selected for mock interview, the chat extracts the **first** `question` field from valid JSON for a single spoken prompt.

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
| `OPENAI_MODEL` | Default model when the client is constructed without an explicit model; can be any preset key (`gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-mini`) or a raw model id | Default: `gpt-4o-mini` |
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

## Reviewers: testing with your own API key

1. Clone the repo and install dependencies (see [Installation and setup](#installation-and-setup)).
2. You can run **without** putting a key in `.env` if you use **BYO** in the app: open the app, choose **Use your own OpenAI API key**, paste your key, and **Apply usage mode**.
3. Alternatively, set `OPENAI_API_KEY` in `.env` and use **Demo mode** so the server uses that key.
4. Run **`pytest tests/unit`** for core checks; optional integration smoke tests need a key in the environment (see [docs/testing.md](docs/testing.md)).

Do not commit `.env` or share keys in issues or screenshots.

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
