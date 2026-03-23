"""Optional NDJSON debug logger for development (one JSON object per line).

Not used in normal user flows; safe to ignore in production. Writes beside the
workspace root path resolved from this file's location.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_LOG_NAME = "debug-f3f979.log"


def _log_path() -> Path:
    # src/interview_app/debug_ndjson.py -> parents[3] = Interview_App workspace root
    return Path(__file__).resolve().parents[3] / _LOG_NAME


def agent_debug_log(
    *,
    location: str,
    message: str,
    data: dict,
    hypothesis_id: str,
    run_id: str = "pre-fix",
) -> None:
    # #region agent log
    payload = {
        "sessionId": "f3f979",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        p = _log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion
