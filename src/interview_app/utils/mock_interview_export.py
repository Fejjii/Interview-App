"""Structured JSON export for mock interview transcripts (UTF-8, serializable)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from interview_app.app.ui_settings import UISettings, label_for_prompt_strategy
from interview_app.utils.types import ChatMessage


def sanitize_export_filename_part(name: str, max_len: int = 48) -> str:
    """Safe single path segment for download filenames (no slashes, control chars)."""
    s = (name or "").strip()
    if not s:
        return "session"
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("._") or "session"
    return s[:max_len]


def build_mock_interview_export_payload(
    *,
    settings: UISettings,
    messages: list[ChatMessage],
    session_title: str,
) -> dict[str, Any]:
    """Shape matches product spec: metadata + generation_config + indexed messages."""
    exported_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    export_messages: list[dict[str, Any]] = []
    for i, m in enumerate(messages, start=1):
        entry: dict[str, Any] = {
            "index": i,
            "role": m.role,
            "content": m.content,
        }
        if m.timestamp:
            entry["timestamp"] = m.timestamp
        export_messages.append(entry)

    return {
        "mode": "mock_interview",
        "exported_at": exported_at,
        "session_name": (session_title or "").strip() or "Untitled session",
        "model": settings.model_preset,
        "persona": settings.persona,
        "prompt_strategy": label_for_prompt_strategy(settings.prompt_strategy),
        "role_context": {
            "category": settings.role_category,
            "seniority": settings.seniority,
            "role_title": settings.role_title,
            "job_description": settings.job_description or "",
        },
        "generation_config": {
            "temperature": float(settings.temperature),
            "top_p": float(settings.top_p),
            "max_tokens": int(settings.max_tokens),
        },
        "messages": export_messages,
    }


def mock_interview_export_filename(session_title: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    part = sanitize_export_filename_part(session_title)
    return f"mock_interview_{part}_{ts}.json"
