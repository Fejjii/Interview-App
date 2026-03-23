"""Redact secret-like substrings before logging or displaying diagnostics."""

from __future__ import annotations

import re
from typing import Final

# OpenAI-style keys and common secret patterns (defensive, not exhaustive).
_SK_LIKE: Final[re.Pattern[str]] = re.compile(
    r"\b(sk-[a-zA-Z0-9_-]{8,}|sk_live_[a-zA-Z0-9]{8,}|sk_test_[a-zA-Z0-9]{8,})\b"
)


def redact_secrets(text: str, *, placeholder: str = "[REDACTED]") -> str:
    """
    Replace substrings that look like API keys or long secret tokens.

    Used for exception messages and debug paths that might echo user-controlled
    or provider content containing key-like material.
    """
    if not text:
        return text
    out = _SK_LIKE.sub(placeholder, text)
    return out
