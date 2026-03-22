from __future__ import annotations

"""Unit tests for safe error handling."""

from interview_app.utils.errors import (
    AppError,
    GuardrailError,
    ModerationError,
    OutputValidationError,
    RateLimitError,
    safe_user_message,
)


def test_app_error_preserves_user_message() -> None:
    err = AppError("Please try again.", internal_detail="NullPointerException at line 42")
    assert safe_user_message(err) == "Please try again."


def test_guardrail_error_user_message() -> None:
    err = GuardrailError("Input rejected by safety checks.")
    assert safe_user_message(err) == "Input rejected by safety checks."


def test_rate_limit_error_user_message() -> None:
    err = RateLimitError("Too many requests.", internal_detail="20 reqs in 60s")
    assert safe_user_message(err) == "Too many requests."


def test_moderation_error_user_message() -> None:
    err = ModerationError("Content blocked by moderation.")
    assert safe_user_message(err) == "Content blocked by moderation."


def test_output_validation_error_user_message() -> None:
    err = OutputValidationError("Model output was empty.")
    assert safe_user_message(err) == "Model output was empty."


def test_generic_exception_returns_safe_fallback() -> None:
    """Unknown exceptions must never leak internals."""
    err = RuntimeError("psycopg2.OperationalError: connection refused at 10.0.0.5:5432")
    msg = safe_user_message(err)
    assert "connection refused" not in msg
    assert "Something went wrong" in msg


def test_timeout_exception_gives_timeout_hint() -> None:
    """Timeout-like exceptions should return a timeout-specific message."""

    class TimeoutError(Exception):
        pass

    msg = safe_user_message(TimeoutError("read timed out"))
    assert "timed out" in msg.lower()


def test_app_error_hierarchy() -> None:
    """All custom errors should be subclasses of AppError."""
    assert issubclass(GuardrailError, AppError)
    assert issubclass(RateLimitError, AppError)
    assert issubclass(ModerationError, AppError)
    assert issubclass(OutputValidationError, AppError)
