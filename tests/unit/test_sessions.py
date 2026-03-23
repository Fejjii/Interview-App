"""Unit tests for JSON session persistence helpers."""

from __future__ import annotations

import hashlib

from interview_app.app.usage_mode import (
    KEY_BYO_OPENAI_API_KEY,
    KEY_USAGE_MODE,
    UsageMode,
)
from interview_app.config.settings import get_settings
from interview_app.storage import sessions as sessions_mod
from interview_app.utils.types import SessionMeta


def _demo_state() -> dict:
    return {KEY_USAGE_MODE: UsageMode.DEMO.value}


def _byo_state(secret: str) -> dict:
    return {
        KEY_USAGE_MODE: UsageMode.BYO.value,
        KEY_BYO_OPENAI_API_KEY: secret,
    }


def test_delete_session_removes_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    sid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    (tmp_path / f"{sid}.json").write_text('{"id": "x", "meta": {}, "messages": []}')
    assert sessions_mod.delete_session(sid, _demo_state()) is True
    assert not (tmp_path / f"{sid}.json").exists()
    get_settings.cache_clear()


def test_delete_session_rejects_unsafe_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    assert sessions_mod.delete_session("../evil", _demo_state()) is False
    assert sessions_mod.delete_session("", _demo_state()) is False
    get_settings.cache_clear()


def test_load_session_rejects_unsafe_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    assert sessions_mod.load_session("..\\evil", _demo_state()) is None
    get_settings.cache_clear()


def test_delete_all_sessions_demo_legacy(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    (tmp_path / "a1b2c3d4-e5f6-7890-abcd-ef1234567890.json").write_text("{}")
    (tmp_path / "b2c3d4e5-f6a7-8901-bcde-f12345678901.json").write_text("{}")
    assert sessions_mod.delete_all_sessions(_demo_state()) == 2
    assert list(tmp_path.glob("*.json")) == []
    get_settings.cache_clear()


def test_list_sessions_scopes_demo_vs_byo(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    demo_sid = "11111111-1111-1111-1111-111111111111"
    byo_sid = "22222222-2222-2222-2222-222222222222"
    (tmp_path / f"{demo_sid}.json").write_text(
        '{"id": "%s", "created_at": "", "title": "D", "meta": {}, "messages": []}' % demo_sid
    )
    k1 = "sk-12345678901234567890123456789012"
    k2 = "sk-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    h1 = hashlib.sha256(k1.encode("utf-8")).hexdigest()
    byo_dir = tmp_path / "byo" / h1
    byo_dir.mkdir(parents=True)
    (byo_dir / f"{byo_sid}.json").write_text(
        '{"id": "%s", "created_at": "", "title": "B", "meta": {}, "messages": []}' % byo_sid
    )

    demo_list = sessions_mod.list_sessions(_demo_state())
    assert len(demo_list) == 1
    assert demo_list[0]["id"] == demo_sid

    byo_list = sessions_mod.list_sessions(_byo_state(k1))
    assert len(byo_list) == 1
    assert byo_list[0]["id"] == byo_sid

    byo_other = sessions_mod.list_sessions(_byo_state(k2))
    assert byo_other == []

    get_settings.cache_clear()


def test_byo_without_key_lists_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    assert sessions_mod.list_sessions({KEY_USAGE_MODE: UsageMode.BYO.value}) == []
    get_settings.cache_clear()


def test_save_session_raises_when_byo_without_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path))
    get_settings.cache_clear()
    meta = SessionMeta(title="x")
    try:
        sessions_mod.save_session(
            None,
            meta,
            [],
            title="t",
            session_state={KEY_USAGE_MODE: UsageMode.BYO.value},
        )
    except RuntimeError as exc:
        assert "BYO" in str(exc) or "key" in str(exc).lower()
    else:
        raise AssertionError("expected RuntimeError")
    get_settings.cache_clear()
