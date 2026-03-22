"""Unit tests for JSON session persistence helpers."""

from __future__ import annotations

from interview_app.config.settings import get_settings
from interview_app.storage import sessions as sessions_mod


def test_delete_session_removes_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    sid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    (tmp_path / f"{sid}.json").write_text('{"id": "x", "meta": {}, "messages": []}')
    assert sessions_mod.delete_session(sid) is True
    assert not (tmp_path / f"{sid}.json").exists()
    get_settings.cache_clear()


def test_delete_session_rejects_unsafe_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    assert sessions_mod.delete_session("../evil") is False
    assert sessions_mod.delete_session("") is False
    get_settings.cache_clear()


def test_load_session_rejects_unsafe_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    assert sessions_mod.load_session("..\\evil") is None
    get_settings.cache_clear()


def test_delete_all_sessions(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    (tmp_path / "a1b2c3d4-e5f6-7890-abcd-ef1234567890.json").write_text("{}")
    (tmp_path / "b2c3d4e5-f6a7-8901-bcde-f12345678901.json").write_text("{}")
    assert sessions_mod.delete_all_sessions() == 2
    assert list(tmp_path.glob("*.json")) == []
    get_settings.cache_clear()
