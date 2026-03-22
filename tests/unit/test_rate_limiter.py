from __future__ import annotations

"""Unit tests for session-based rate limiting."""

import pytest

from interview_app.security.rate_limiter import (
    RateLimitResult,
    check_rate_limit,
    reset_rate_limit,
    _SESSION_KEY,
)


def test_allows_requests_within_limit() -> None:
    """Requests below the limit should be allowed."""
    session: dict = {}
    for _ in range(3):
        result = check_rate_limit(session, max_requests=5, window_seconds=60)
        assert result.allowed is True
    assert result.current_count == 3


def test_blocks_when_limit_exceeded() -> None:
    """The Nth+1 request should be blocked."""
    session: dict = {}
    for _ in range(3):
        check_rate_limit(session, max_requests=3, window_seconds=60)

    result = check_rate_limit(session, max_requests=3, window_seconds=60)
    assert result.allowed is False
    assert "too quickly" in result.message.lower()
    assert result.retry_after_seconds >= 0


def test_none_session_state_always_allows() -> None:
    """When no session_state is provided, rate limiting is a no-op."""
    result = check_rate_limit(None, max_requests=1, window_seconds=60)
    assert result.allowed is True


def test_reset_clears_history() -> None:
    """Resetting should clear the timestamps and allow new requests."""
    session: dict = {}
    for _ in range(5):
        check_rate_limit(session, max_requests=5, window_seconds=60)

    blocked = check_rate_limit(session, max_requests=5, window_seconds=60)
    assert blocked.allowed is False

    reset_rate_limit(session)
    assert _SESSION_KEY not in session

    result = check_rate_limit(session, max_requests=5, window_seconds=60)
    assert result.allowed is True


def test_expired_timestamps_are_pruned() -> None:
    """Timestamps older than the window should not count toward the limit."""
    import time

    session: dict = {}
    # Manually inject an "old" timestamp far in the past
    session[_SESSION_KEY] = [time.monotonic() - 200]

    result = check_rate_limit(session, max_requests=1, window_seconds=60)
    assert result.allowed is True
    assert result.current_count == 1


def test_result_model_fields() -> None:
    """RateLimitResult should carry the expected metadata."""
    session: dict = {}
    result = check_rate_limit(session, max_requests=10, window_seconds=30)
    assert isinstance(result, RateLimitResult)
    assert result.limit == 10
    assert result.window_seconds == 30
