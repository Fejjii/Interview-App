from __future__ import annotations

"""
Session-based rate limiting.

Uses a simple in-memory list of timestamps (designed for Streamlit session state
or plain dict). No external dependencies required.
"""

import time
from typing import Any

from pydantic import BaseModel

from interview_app.config.settings import get_security_settings
from interview_app.security.logging import log_security_event


class RateLimitResult(BaseModel):
    """Outcome of a rate-limit check."""

    allowed: bool
    current_count: int = 0
    limit: int = 0
    window_seconds: int = 0
    retry_after_seconds: float = 0.0
    message: str = ""


_SESSION_KEY = "_security_rate_limit_timestamps"


def check_rate_limit(
    session_state: dict[str, Any] | None = None,
    *,
    max_requests: int | None = None,
    window_seconds: int | None = None,
    service: str = "unknown",
) -> RateLimitResult:
    """
    Check whether the current session has exceeded its request budget.

    Args:
        session_state: A mutable dict (e.g. ``st.session_state``).  When
            ``None``, rate limiting is effectively a no-op (always allowed).
        max_requests: Override from config if provided.
        window_seconds: Override from config if provided.
        service: Name used in security logs.

    Returns:
        RateLimitResult with ``allowed=True`` when within limits.
    """
    sec = get_security_settings()
    limit = max_requests if max_requests is not None else sec.rate_limit_max_requests
    window = window_seconds if window_seconds is not None else sec.rate_limit_window_seconds

    if session_state is None:
        return RateLimitResult(allowed=True, limit=limit, window_seconds=window)

    now = time.monotonic()
    timestamps: list[float] = session_state.get(_SESSION_KEY, [])

    cutoff = now - window
    timestamps = [t for t in timestamps if t > cutoff]

    if len(timestamps) >= limit:
        oldest = min(timestamps) if timestamps else now
        retry_after = oldest + window - now
        log_security_event(
            event="rate_limit",
            action="blocked",
            reason=f"{len(timestamps)} requests in {window}s (limit {limit})",
            service=service,
        )
        session_state[_SESSION_KEY] = timestamps
        return RateLimitResult(
            allowed=False,
            current_count=len(timestamps),
            limit=limit,
            window_seconds=window,
            retry_after_seconds=max(0.0, retry_after),
            message=(
                f"You're sending requests too quickly. "
                f"Please wait {int(retry_after) + 1} seconds before trying again."
            ),
        )

    timestamps.append(now)
    session_state[_SESSION_KEY] = timestamps

    return RateLimitResult(
        allowed=True,
        current_count=len(timestamps),
        limit=limit,
        window_seconds=window,
    )


def reset_rate_limit(session_state: dict[str, Any]) -> None:
    """Clear the rate-limit history (e.g. on session reset)."""
    session_state.pop(_SESSION_KEY, None)
