from __future__ import annotations

"""
Structured security event logging.

Logs security-relevant events (blocks, warnings, rate-limit hits) with a
consistent JSON-like structure for auditability. Sensitive data (secrets, raw
API keys, full user text) is never included in log output.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("interview_app.security")


def log_security_event(
    *,
    event: str,
    action: str,
    reason: str,
    service: str = "unknown",
    matched_pattern: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Emit a structured security log entry.

    Args:
        event: Category of the security event (e.g. "rate_limit", "moderation",
               "prompt_injection", "output_guard").
        action: "blocked" or "allowed".
        reason: Human-readable explanation (no secrets).
        service: Calling service or module name.
        matched_pattern: Optional pattern that triggered the event (truncated
                         to avoid leaking full user text).
        extra: Any additional safe metadata.
    """
    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "action": action,
        "reason": reason,
        "service": service,
    }
    if matched_pattern is not None:
        entry["matched_pattern"] = matched_pattern[:120]
    if extra:
        entry["extra"] = extra

    if action == "blocked":
        logger.warning("SECURITY %s", entry)
    else:
        logger.info("SECURITY %s", entry)
