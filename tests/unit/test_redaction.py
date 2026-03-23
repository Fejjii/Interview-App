"""Secret redaction for logs and diagnostics."""

from __future__ import annotations

from interview_app.security.redaction import redact_secrets


def test_redact_sk_like_strings() -> None:
    raw = "failed: sk-12345678901234567890123456789012 end"
    out = redact_secrets(raw)
    assert "sk-12345678901234567890123456789012" not in out
    assert "[REDACTED]" in out
