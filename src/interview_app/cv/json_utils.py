from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def extract_json_object(raw: str) -> str:
    """
    Strip optional markdown fences and return a JSON object/array string.

    Raises ValueError if no plausible JSON payload is found.
    """
    text = (raw or "").strip()
    if not text:
        raise ValueError("Empty model output.")

    m = _JSON_FENCE_RE.search(text)
    if m:
        text = m.group(1).strip()

    # If still wrapped in prose, try first { ... } or [ ... ] span (greedy balance simple case).
    if not (text.startswith("{") or text.startswith("[")):
        start_obj = text.find("{")
        start_arr = text.find("[")
        candidates = [i for i in (start_obj, start_arr) if i >= 0]
        if candidates:
            start = min(candidates)
            text = text[start:].strip()

    return text


def parse_llm_json_model(raw: str, model_type: type[T]) -> T:
    """Parse JSON from LLM output and validate with the given Pydantic model."""
    payload = extract_json_object(raw)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    try:
        return model_type.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"JSON does not match schema: {exc}") from exc
