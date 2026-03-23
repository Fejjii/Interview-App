"""Parse model output for interview question generation (e.g. structured JSON)."""

from __future__ import annotations

import json
import re
from typing import Any


def _strip_json_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def try_parse_questions_json(text: str) -> list[dict[str, Any]] | None:
    """
    If ``text`` is valid JSON with a ``questions`` array of objects, return it.

    Returns None if parsing fails or structure is unexpected.
    """
    raw = _strip_json_fences(text)
    if not raw or raw[0] not in "{[":
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    items = data.get("questions")
    if not isinstance(items, list) or not items:
        return None
    out: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict) and "question" in item:
            out.append(item)
    return out if out else None


def first_question_text_from_output(text: str) -> str | None:
    """Best-effort: first question string for chat UI (structured JSON or plain text)."""
    parsed = try_parse_questions_json(text)
    if parsed:
        q = parsed[0].get("question")
        if isinstance(q, str) and q.strip():
            return q.strip()
    return None


_NUM_LINE = re.compile(r"^(\d+)(?:\.\d+)?[\.\)]\s+(.+)$")


def _extract_numbered_list_items(text: str) -> list[str]:
    """Split a numbered list into question strings (supports simple continuations)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    items: list[str] = []
    for line in lines:
        m = _NUM_LINE.match(line)
        if m:
            items.append(m.group(2).strip())
        elif items and not _NUM_LINE.match(line):
            items[-1] = (items[-1] + " " + line).strip()
    return items


def parse_generation_questions_list(text: str, strategy_key: str = "") -> list[str]:
    """
    Normalize model output to a list of question strings for side-by-side comparison.

    Uses JSON ``questions[].question`` when valid; otherwise parses numbered lines.
    ``strategy_key`` is reserved for future strategy-specific parsing (unused today).
    """
    _ = strategy_key
    parsed = try_parse_questions_json(text)
    if parsed:
        out = [str(x.get("question", "")).strip() for x in parsed]
        return [q for q in out if q]
    raw = (text or "").strip()
    if not raw:
        return []
    numbered = _extract_numbered_list_items(raw)
    if numbered:
        return numbered
    return [raw]
