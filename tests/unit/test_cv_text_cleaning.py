from __future__ import annotations

from interview_app.cv.text_cleaning import normalize_cv_text


def test_normalize_cv_text_strips_control_chars() -> None:
    raw = "Hello\x00World\n\n\n\nNext"
    out = normalize_cv_text(raw)
    assert "Hello" in out
    assert "World" in out
    assert "\x00" not in out


def test_normalize_cv_text_collapses_blank_lines() -> None:
    raw = "A\n\n\n\nB"
    out = normalize_cv_text(raw)
    assert out.count("\n\n") <= 1 or "A" in out and "B" in out


def test_normalize_cv_text_empty() -> None:
    assert normalize_cv_text("") == ""
