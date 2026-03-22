from __future__ import annotations

"""Unit tests for structured security logging."""

import logging

from interview_app.security.logging import log_security_event


def test_blocked_event_logs_at_warning(caplog: logging.LogRecord) -> None:
    with caplog.at_level(logging.WARNING, logger="interview_app.security"):
        log_security_event(
            event="moderation",
            action="blocked",
            reason="hate_speech detected",
            service="test",
            matched_pattern="racist joke",
        )
    assert "SECURITY" in caplog.text
    assert "moderation" in caplog.text
    assert "blocked" in caplog.text


def test_allowed_event_logs_at_info(caplog: logging.LogRecord) -> None:
    with caplog.at_level(logging.INFO, logger="interview_app.security"):
        log_security_event(
            event="rate_limit",
            action="allowed",
            reason="within limits",
            service="test",
        )
    assert "SECURITY" in caplog.text
    assert "allowed" in caplog.text


def test_matched_pattern_truncated(caplog: logging.LogRecord) -> None:
    long_pattern = "x" * 200
    with caplog.at_level(logging.WARNING, logger="interview_app.security"):
        log_security_event(
            event="test",
            action="blocked",
            reason="test",
            service="test",
            matched_pattern=long_pattern,
        )
    # The pattern should be truncated to 120 chars in the log
    assert long_pattern not in caplog.text
