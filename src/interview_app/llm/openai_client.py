from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from interview_app.config.settings import Settings, get_settings
from interview_app.llm.model_settings import MODEL_PRESETS, ModelConfig
from interview_app.utils.types import LLMResponse, LLMUsage


@dataclass(frozen=True)
class ClientParams:
    model: str
    temperature: float
    top_p: float | None
    max_tokens: int | None


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
        self._settings = settings or get_settings()

        resolved_key = api_key or (
            self._settings.openai_api_key.get_secret_value()
            if self._settings.openai_api_key is not None
            else None
        )
        # #region agent log
        import json
        from pathlib import Path
        _log = Path(__file__).resolve().parents[4] / "debug-0cdc00.log"
        with open(_log, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({"hypothesisId": "B", "location": "openai_client.py:LLMClient.__init__", "message": "key_resolution", "data": {"settings_key_is_none": self._settings.openai_api_key is None, "resolved_key_set": bool(resolved_key and str(resolved_key).strip())}, "timestamp": __import__("time").time() * 1000}) + "\n")
        # #endregion
        if not (resolved_key and str(resolved_key).strip()):
            raise ValueError(
                "OpenAI API key is missing. Set OPENAI_API_KEY in a .env file (copy .env.example to .env) "
                "or as an environment variable. Do not commit .env to version control."
            )
        self._client = OpenAI(api_key=resolved_key.strip())
        self._timeout_s = timeout_s

        preset: ModelConfig | None = MODEL_PRESETS.get(self._settings.openai_model)  # type: ignore[arg-type]
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
    ) -> LLMResponse:
        """
        Generate a single assistant response from system + user prompts.

        `extra_messages` can be used to pass additional chat turns in OpenAI's
        `{role, content}` shape, e.g. prior user/assistant messages.
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
            messages = messages[:-1] + extra_messages + messages[-1:]

        resp = self._client.chat.completions.create(
            model=resolved.model,
            messages=messages,
            temperature=resolved.temperature,
            top_p=resolved.top_p,
            max_tokens=resolved.max_tokens,
            timeout=self._timeout_s,
        )

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

        return LLMResponse(
            text=text,
            model=getattr(resp, "model", resolved.model),
            usage=usage,
            raw_response_id=getattr(resp, "id", None),
        )

