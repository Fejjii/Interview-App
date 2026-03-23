"""OpenAI SDK adapter: single entry point for chat completions from services.

Isolates OpenAI-specific types and request shaping. Callers use
``LLMClient.generate_response`` and receive ``LLMResponse`` (see ``utils.types``).

Each successful or failed call writes a **structured audit log** (model, latency,
token counts, route label)—never full prompt text. Fits between ``services/`` and
the external OpenAI HTTP API.

Raises:
    ValueError: If no API key can be resolved from settings or constructor args.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from interview_app.config.settings import Settings, get_settings
from interview_app.llm.model_settings import MODEL_PRESETS, ModelConfig, is_model_preset_key
from interview_app.utils.types import LLMResponse, LLMUsage

logger = logging.getLogger("interview_app.llm")


@dataclass(frozen=True)
class ClientParams:
    """Resolved parameters for a single OpenAI request (after defaults are applied)."""

    model: str
    temperature: float
    top_p: float | None
    max_tokens: int | None


def _log_llm_audit(
    *,
    llm_route: str | None,
    model: str,
    success: bool,
    latency_ms: float,
    usage: LLMUsage | None,
    error_type: str | None = None,
) -> None:
    """Structured boundary log: model, tokens, latency, outcome. Never logs prompt text."""
    entry: dict[str, Any] = {
        "event": "llm_call",
        "route": llm_route or "unknown",
        "model": model,
        "success": success,
        "latency_ms": round(latency_ms, 2),
    }
    if usage is not None:
        entry["prompt_tokens"] = usage.prompt_tokens
        entry["completion_tokens"] = usage.completion_tokens
        entry["total_tokens"] = usage.total_tokens
    if error_type:
        entry["error_type"] = error_type

    if success:
        logger.info("LLM %s", entry)
    else:
        logger.warning("LLM %s", entry)


class LLMClient:
    """
    Thin wrapper around the OpenAI Python SDK (v1+).

    This keeps OpenAI-specific details isolated so the rest of the app can call
    `generate_response(system_prompt, user_prompt)` and receive a structured response.
    """

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float | None = 60.0,
    ) -> None:
        """
        Create an OpenAI client with reasonable defaults.

        Resolution order:
        - explicit constructor args (model/temperature/…)
        - matching preset defaults (if `Settings.openai_model` is a preset key)
        - fallback to raw `Settings` values
        """
        self._settings = settings or get_settings()

        resolved_key = api_key or (
            self._settings.openai_api_key.get_secret_value()
            if self._settings.openai_api_key is not None
            else None
        )
        if not (resolved_key and str(resolved_key).strip()):
            raise ValueError(
                "OpenAI API key is missing. Set OPENAI_API_KEY in a .env file (copy .env.example to .env) "
                "or as an environment variable. Do not commit .env to version control."
            )
        self._client = OpenAI(api_key=resolved_key.strip())
        self._timeout_s = timeout_s

        # If the configured model is one of our presets, use its defaults for temperature/max_tokens.
        preset_key = self._settings.openai_model
        preset: ModelConfig | None = MODEL_PRESETS.get(preset_key) if is_model_preset_key(preset_key) else None
        self._defaults = ClientParams(
            model=model or (preset.name if preset else self._settings.openai_model),
            temperature=temperature if temperature is not None else (preset.default_temperature if preset else self._settings.openai_temperature),
            top_p=top_p if top_p is not None else (preset.default_top_p if preset else None),
            max_tokens=max_tokens if max_tokens is not None else (preset.default_max_tokens if preset else None),
        )

    def generate_response(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        extra_messages: list[dict[str, Any]] | None = None,
        llm_route: str | None = None,
    ) -> LLMResponse:
        """
        Generate a single assistant response from system + user prompts.

        `extra_messages` can be used to pass additional chat turns in OpenAI's
        `{role, content}` shape, e.g. prior user/assistant messages.

        `llm_route` identifies the call site for audit logs (e.g. ``interview_generator``).
        """
        resolved = ClientParams(
            model=model or self._defaults.model,
            temperature=temperature if temperature is not None else self._defaults.temperature,
            top_p=top_p if top_p is not None else self._defaults.top_p,
            max_tokens=max_tokens if max_tokens is not None else self._defaults.max_tokens,
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if extra_messages:
            # Insert extra messages between system and the final user prompt.
            messages = messages[:-1] + extra_messages + messages[-1:]

        t0 = time.monotonic()
        try:
            # Single-shot Chat Completions call (kept intentionally simple for this project).
            resp = self._client.chat.completions.create(
                model=resolved.model,
                messages=messages,
                temperature=resolved.temperature,
                top_p=resolved.top_p,
                max_tokens=resolved.max_tokens,
                timeout=self._timeout_s,
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - t0) * 1000.0
            _log_llm_audit(
                llm_route=llm_route,
                model=resolved.model,
                success=False,
                latency_ms=latency_ms,
                usage=None,
                error_type=type(exc).__name__,
            )
            raise

        latency_ms = (time.monotonic() - t0) * 1000.0
        text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        usage = (
            LLMUsage(
                prompt_tokens=getattr(resp.usage, "prompt_tokens", None),
                completion_tokens=getattr(resp.usage, "completion_tokens", None),
                total_tokens=getattr(resp.usage, "total_tokens", None),
            )
            if getattr(resp, "usage", None) is not None
            else None
        )

        _log_llm_audit(
            llm_route=llm_route,
            model=getattr(resp, "model", resolved.model),
            success=True,
            latency_ms=latency_ms,
            usage=usage,
        )

        return LLMResponse(
            text=text,
            model=getattr(resp, "model", resolved.model),
            usage=usage,
            raw_response_id=getattr(resp, "id", None),
        )
