# Security gap fix — pre-change audit

## Existing implementation locations

| Area | Location |
|------|----------|
| Chat conversational LLM | `src/interview_app/services/chat_service.py` — `_answer_general_question` |
| System prompt hardening | `src/interview_app/security/guards.py` — `protect_system_prompt` |
| Interview / evaluator | `interview_generator.py`, `answer_evaluator.py`, `cv/prompt_builders.py` — `protect_system_prompt` on system prompts |
| Input pipeline | `src/interview_app/security/pipeline.py` — `run_input_pipeline` → `run_guardrails` |
| Output pipeline | `pipeline.py` — `run_output_pipeline` → `output_guard.validate_output` |
| Strict setting (was unused) | `src/interview_app/config/settings.py` — `SecuritySettings.prompt_injection_strict` |
| Security logging | `src/interview_app/security/logging.py` — `log_security_event` |
| Rate limit | `rate_limiter.py` — `check_rate_limit`; invoked from `run_input_pipeline` when `check_rate=True` |
| LLM boundary | `src/interview_app/llm/openai_client.py` — `LLMClient.generate_response` |
| Secret redaction | `guards.py` — `sanitize_user_input`, `_SECRET_REGEXES` |

## Confirmed gaps (before fix)

1. **`_answer_general_question`**: no `protect_system_prompt`, no `run_output_pipeline`.
2. **`prompt_injection_strict`**: defined but not read by injection detection.
3. **Injection blocks**: no `log_security_event` on block (only moderation/rate/output_guard).
4. **Chat → nested services**: `run_turn` rate-limits the chat message, then `generate_questions` / `evaluate_answer` rate-limit again on `role_title` / `question`.
5. **LLM calls**: no structured audit log (model, tokens, latency, success) at client.
6. **Secret patterns**: limited to sk-, PEM, AKIA; missing common bearer/GitHub-style tokens.
7. **Output guard**: patterns included `Security: Never reveal`, conflicting with appended `protect_system_prompt` text (false-positive risk).

## Proposed change points

- `guards.py`: wire strict mode, expand redaction, log injection via `log_security_event`, pass service from pipeline.
- `pipeline.py`: pass `service` into `run_guardrails`.
- `chat_service.py`: `protect_system_prompt` + `run_output_pipeline`; pass `skip_session_rate_limit=True` into nested services.
- `interview_generator.py` / `answer_evaluator.py`: `skip_session_rate_limit` flag controlling `check_rate` on session-scoped pipelines.
- `openai_client.py`: optional `llm_route`, timing, structured LLM audit log (no prompt content).
- `output_guard.py`: remove self-conflicting leakage patterns tied to our own security suffix.
- `cv_interview_service.py`: pass `llm_route` on `generate_response` calls.

## Resolution status

Implemented in the same codebase pass; see `docs/security_fix_validation_report.md` for test results and manual checklist.
