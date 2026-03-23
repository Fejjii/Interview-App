"""Local JSON persistence for saved mock interview sessions.

Files live under ``SESSIONS_DIR`` (see settings); each session is one ``*.json``
with metadata and message list. Used by sidebar session controls and ``layout``.

Security: session IDs are validated to prevent path traversal on load/delete.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from interview_app.config.settings import get_settings
from interview_app.utils.types import SessionMeta


def _sessions_path() -> Path:
    p = Path(get_settings().sessions_dir)
    if not p.is_absolute():
        p = Path.cwd() / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def _is_safe_session_id(session_id: str) -> bool:
    """Reject path traversal and odd filenames; session ids are UUIDs."""
    if not session_id or len(session_id) > 128:
        return False
    if ".." in session_id or "/" in session_id or "\\" in session_id:
        return False
    return all(c.isalnum() or c in "-_" for c in session_id)


def _file_for(session_id: str) -> Path:
    return _sessions_path() / f"{session_id}.json"


def get_session_file_path(session_id: str) -> Path:
    """Return the absolute path of the JSON file for a session (for display to the user)."""
    return _file_for(session_id).resolve()


def list_sessions() -> list[dict]:
    """
    List past sessions (id, created_at, title, meta).
    Returns list of dicts with keys: id, created_at, title, meta (SessionMeta dict).
    """
    path = _sessions_path()
    out = []
    for f in sorted(path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out.append({
                "id": data.get("id", f.stem),
                "created_at": data.get("created_at", ""),
                "title": data.get("title", "Untitled"),
                "meta": data.get("meta", {}),
            })
        except Exception:
            continue
    return out


def load_session(session_id: str) -> tuple[SessionMeta, list[dict]] | None:
    """
    Load a session by id. Returns (SessionMeta, messages) or None if not found.
    messages are list of {role, content}.
    """
    if not _is_safe_session_id(session_id):
        return None
    f = _file_for(session_id)
    if not f.exists():
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
) -> str:
    """
    Save session to JSON. If session_id is None, generate a new UUID.
    messages should be list of {role, content}. Returns the session id used.
    """
    sid = session_id or str(uuid4())
    out_file = _file_for(sid)
    meta_dict = meta.model_dump()
    if not meta_dict.get("id"):
        meta_dict["id"] = sid
    if title:
        meta_dict["title"] = title
    payload = {
        "id": sid,
        "created_at": meta_dict.get("created_at", ""),
        "title": meta_dict.get("title", "Untitled session"),
        "meta": meta_dict,
        "messages": messages,
    }
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return sid


def delete_session(session_id: str) -> bool:
    """
    Remove one session file. Returns True if a file was deleted.
    """
    if not _is_safe_session_id(session_id):
        return False
    f = _file_for(session_id)
    if not f.is_file():
        return False
    try:
        f.unlink()
        return True
    except OSError:
        return False


def delete_all_sessions() -> int:
    """
    Delete every *.json session file in the sessions directory. Returns count removed.
    """
    path = _sessions_path()
    n = 0
    for f in path.glob("*.json"):
        try:
            f.unlink()
            n += 1
        except OSError:
            continue
    return n
