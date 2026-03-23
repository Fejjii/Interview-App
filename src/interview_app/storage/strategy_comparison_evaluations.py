"""Append-only local JSON log for strategy comparison user evaluations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from interview_app.config.settings import get_settings


def _file_path() -> Path:
    sessions = Path(get_settings().sessions_dir)
    if not sessions.is_absolute():
        sessions = Path.cwd() / sessions
    root = sessions.parent if sessions.name == "sessions" else sessions
    root.mkdir(parents=True, exist_ok=True)
    return root / "strategy_comparison_evaluations.json"


def append_evaluation(record: dict[str, Any]) -> Path:
    """
    Append one evaluation record to the JSON array file. Creates the file if missing.

    Adds ``saved_at`` (UTC ISO) if not present.
    """
    path = _file_path()
    if "saved_at" not in record:
        record = {**record, "saved_at": datetime.now(timezone.utc).isoformat()}
    data: list[Any] = []
    if path.exists():
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw) if raw.strip() else []
        except (json.JSONDecodeError, OSError):
            data = []
    if not isinstance(data, list):
        data = []
    data.append(record)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
