# Security

This document summarizes how the Interview App handles untrusted input, what guarantees are realistic for a **Streamlit desktop-style deployment**, and how to tune behavior via environment variables.

---

## Threat model (practical)

- **Assumption:** The person running the app is the same person entering data (local or trusted single-user use). The UI is **not** a hardened multi-tenant API.
- **Goals:** Reduce accidental data leakage, block obvious prompt-injection attempts from reaching the model, limit abuse via rate limits, and avoid logging secrets or full prompts in structured audit lines.

For internet-facing multi-user products, add an **authenticated backend**, server-side quotas, and independent validation—do not rely on client-side guardrails alone.

---

## Defense layers

### 1. Input validation and sanitization (`security/guards.py`)

- Non-empty checks and maximum length.
- **Secret redaction** heuristics for API-key-like strings, PEM blocks, and common token patterns (best-effort; not exhaustive).
- **Prompt-injection heuristics:** phrase lists and regexes; optional **strict** mode for additional patterns (more false positives).

### 2. Pre-LLM pipeline (`security/pipeline.py`)

Ordered checks via `run_input_pipeline`:

1. Guardrails (validation + redaction + injection detection).
2. Lightweight **moderation** (`security/moderation.py`) when enabled.
3. **Rate limiting** (`security/rate_limiter.py`) when `session_state` is provided and `check_rate=True`.

Nested service calls (e.g. chat calling `interview_generator`) may pass **`skip_session_rate_limit`**-style flags to avoid double-counting one user-visible action—see implementation in each service.

### 3. Post-LLM output checks (`security/output_guard.py`)

Invoked through `run_output_pipeline`: empty responses, excessive length, optional JSON validation, and basic leakage heuristics as implemented.

### 4. System prompt hardening

`protect_system_prompt` and related helpers reduce trivial instruction-overwrite patterns in constructed system strings where used.

### 5. Logging (`security/logging.py`)

Structured security events for blocked or flagged actions. **Do not** log full user prompts or secrets in production without policy review.

### 6. LLM audit (`llm/openai_client.py`)

Boundary logs include model, latency, token counts, and success/failure—not raw prompt text.

---

## Environment variables (security-related)

All use the `SECURITY_` prefix (see `SecuritySettings` in `config/settings.py`):

| Variable | Purpose |
|----------|---------|
| `SECURITY_MAX_INPUT_LENGTH` | Max characters per guarded input field (default 8000). |
| `SECURITY_OUTPUT_MAX_LENGTH` | Max model output length before truncation. |
| `SECURITY_RATE_LIMIT_MAX_REQUESTS` | Max LLM-bound requests per window. |
| `SECURITY_RATE_LIMIT_WINDOW_SECONDS` | Sliding window for rate limit. |
| `SECURITY_MODERATION_ENABLED` | Toggle lightweight moderation step. |
| `SECURITY_PROMPT_INJECTION_STRICT` | Stricter injection detection (more false positives). |
| `SECURITY_CV_MAX_FILE_BYTES` | Max upload size for CV files. |
| `SECURITY_CV_MAX_TEXT_CHARS` | Max extracted CV text sent to guardrails/LLM. |

Global app settings: `OPENAI_API_KEY` (secret), `SESSIONS_DIR` (where JSON sessions are written—keep on trusted storage).

---

## Operational notes

- **`.env`** must remain **gitignored**; rotate keys if exposed.
- **Session JSON** may contain interview content; treat `data/sessions/` as sensitive if deployed on shared disks.
- **Dependencies:** Keep `requirements.txt` / `pyproject.toml` pinned or reviewed for known CVEs in production.

---

## Verification

- Automated: `pytest tests/unit` (guardrails, pipeline, moderation, rate limiter).
- Manual: see [testing.md](testing.md) (manual guardrail checks).

---

## Related documentation

- [architecture.md](architecture.md) — where security sits in the stack.
- [testing.md](testing.md) — automated and manual verification.
