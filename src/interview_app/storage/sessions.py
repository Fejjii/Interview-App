"""Local JSON persistence for saved mock interview sessions.

Files are **scoped** by usage mode so Demo and BYO (and distinct BYO keys) do not
share the same saved-session list:

- ``demo/`` — sessions saved while using Demo mode (server key)
- ``byo/<sha256>/`` — sessions saved while using a specific BYO key (hash of key)
- Legacy flat ``*.json`` at the sessions root are treated as Demo-only history

Security: session IDs are validated to prevent path traversal on load/delete.
BYO scope uses SHA-256 of the key for directory names only; the key is never written here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from interview_app.app.usage_mode import (
    KEY_BYO_OPENAI_API_KEY,
    KEY_USAGE_MODE,
    UsageMode,
)
from interview_app.config.settings import get_settings
from interview_app.utils.types import SessionMeta


def _sessions_base() -> Path:
    p = Path(get_settings().sessions_dir)
    if not p.is_absolute():
        p = Path.cwd() / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def _byo_scope_dir_name(secret: str) -> str:
    return hashlib.sha256(secret.strip().encode("utf-8")).hexdigest()


def _scope_tag(session_state: dict[str, Any]) -> str:
    """Serializable tag stored in JSON (no secrets)."""
    mode = str(session_state.get(KEY_USAGE_MODE) or UsageMode.DEMO.value)
    if mode != UsageMode.BYO.value:
        return "demo"
    raw = session_state.get(KEY_BYO_OPENAI_API_KEY)
    if not isinstance(raw, str) or not raw.strip():
        return "byo:unbound"
    return f"byo:{_byo_scope_dir_name(raw)}"


def _scoped_storage_dir(session_state: dict[str, Any]) -> Path | None:
    """
    Directory containing session JSON files for the current scope.

    Returns None when BYO is selected but no key is present (no saved sessions).
    """
    mode = str(session_state.get(KEY_USAGE_MODE) or UsageMode.DEMO.value)
    base = _sessions_base()
    if mode != UsageMode.BYO.value:
        d = base / "demo"
        d.mkdir(parents=True, exist_ok=True)
        return d
    raw = session_state.get(KEY_BYO_OPENAI_API_KEY)
    if not isinstance(raw, str) or not raw.strip():
        return None
    d = base / "byo" / _byo_scope_dir_name(raw)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _is_safe_session_id(session_id: str) -> bool:
    """Reject path traversal and odd filenames; session ids are UUIDs."""
    if not session_id or len(session_id) > 128:
        return False
    if ".." in session_id or "/" in session_id or "\\" in session_id:
        return False
    return all(c.isalnum() or c in "-_" for c in session_id)


def _iter_demo_session_files(base: Path) -> list[Path]:
    """Legacy root *.json plus ``demo/*.json`` (Demo scope only)."""
    files: list[Path] = []
    for f in base.glob("*.json"):
        files.append(f)
    demo_sub = base / "demo"
    if demo_sub.is_dir():
        for f in demo_sub.glob("*.json"):
            files.append(f)
    return files


def _find_session_file(session_id: str, session_state: dict[str, Any]) -> Path | None:
    if not _is_safe_session_id(session_id):
        return None
    scoped = _scoped_storage_dir(session_state)
    if scoped is not None:
        candidate = scoped / f"{session_id}.json"
        if candidate.is_file():
            return candidate
    mode = str(session_state.get(KEY_USAGE_MODE) or UsageMode.DEMO.value)
    if mode == UsageMode.DEMO.value:
        legacy = _sessions_base() / f"{session_id}.json"
        if legacy.is_file():
            return legacy
    return None


def get_session_file_path(session_id: str, session_state: dict[str, Any]) -> Path:
    """Return the absolute path of the JSON file for a session (for display to the user)."""
    found = _find_session_file(session_id, session_state)
    if found is not None:
        return found.resolve()
    scoped = _scoped_storage_dir(session_state)
    if scoped is not None:
        return (scoped / f"{session_id}.json").resolve()
    return (_sessions_base() / "demo" / f"{session_id}.json").resolve()


def list_sessions(session_state: dict[str, Any]) -> list[dict]:
    """
    List past sessions (id, created_at, title, meta) for the **current** scope only.

    Demo scope includes legacy flat ``*.json`` files at the sessions root.
    BYO scope lists only files for the active BYO key; empty if no key is set.
    """
    scoped = _scoped_storage_dir(session_state)
    if scoped is None:
        return []

    mode = str(session_state.get(KEY_USAGE_MODE) or UsageMode.DEMO.value)
    if mode == UsageMode.DEMO.value:
        files = _iter_demo_session_files(_sessions_base())
    else:
        files = list(scoped.glob("*.json"))

    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    out = []
    seen_ids: set[str] = set()
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sid = str(data.get("id", f.stem))
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            out.append(
                {
                    "id": sid,
                    "created_at": data.get("created_at", ""),
                    "title": data.get("title", "Untitled"),
                    "meta": data.get("meta", {}),
                }
            )
        except Exception:
            continue
    return out


def load_session(
    session_id: str, session_state: dict[str, Any]
) -> tuple[SessionMeta, list[dict]] | None:
    """
    Load a session by id within the current scope. Returns (SessionMeta, messages) or None.
    messages are list of {role, content}.
    """
    f = _find_session_file(session_id, session_state)
    if f is None:
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        meta = SessionMeta.model_validate(data.get("meta", {}))
        messages = data.get("messages", [])
        return meta, messages
    except Exception:
        return None


def save_session(
    session_id: str | None,
    meta: SessionMeta,
    messages: list[dict],
    title: str = "",
    *,
    session_state: dict[str, Any],
) -> str:
    """
    Save session to JSON in the current usage scope. If session_id is None, generate UUID.

    messages should be list of {role, content}. Returns the session id used.
    """
    scoped = _scoped_storage_dir(session_state)
    if scoped is None:
        raise RuntimeError("Cannot save session: BYO mode requires an applied API key.")

    sid = session_id or str(uuid4())
    out_file = scoped / f"{sid}.json"
    meta_dict = meta.model_dump()
    if not meta_dict.get("id"):
        meta_dict["id"] = sid
    if title:
        meta_dict["title"] = title
    scope_tag = _scope_tag(session_state)
    payload = {
        "id": sid,
        "created_at": meta_dict.get("created_at", ""),
        "title": meta_dict.get("title", "Untitled session"),
        "meta": meta_dict,
        "messages": messages,
        "usage_scope": scope_tag,
    }
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Drop legacy root duplicate after migrating into demo/ (same session id).
    if str(session_state.get(KEY_USAGE_MODE) or UsageMode.DEMO.value) == UsageMode.DEMO.value:
        legacy = _sessions_base() / f"{sid}.json"
        if legacy.is_file() and legacy.resolve() != out_file.resolve():
            try:
                legacy.unlink()
            except OSError:
                pass

    return sid


def delete_session(session_id: str, session_state: dict[str, Any]) -> bool:
    """
    Remove one session file within the current scope. Returns True if a file was deleted.
    """
    f = _find_session_file(session_id, session_state)
    if f is None or not f.is_file():
        return False
    try:
        f.unlink()
        return True
    except OSError:
        return False


def delete_all_sessions(session_state: dict[str, Any]) -> int:
    """
    Delete every session file in the **current** scope only.

    Demo: legacy root ``*.json`` plus ``demo/*.json``. Does not remove BYO directories.
    BYO: only the folder for the active key.
    """
    scoped = _scoped_storage_dir(session_state)
    if scoped is None:
        return 0

    mode = str(session_state.get(KEY_USAGE_MODE) or UsageMode.DEMO.value)
    n = 0
    if mode == UsageMode.DEMO.value:
        base = _sessions_base()
        for f in _iter_demo_session_files(base):
            try:
                f.unlink()
                n += 1
            except OSError:
                continue
    else:
        for f in scoped.glob("*.json"):
            try:
                f.unlink()
                n += 1
            except OSError:
                continue
    return n
