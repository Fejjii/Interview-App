"""
Streamlit session state for the CV interview-prep workspace.

Keeps a single namespace of keys so we can reset cleanly and avoid stale UI.
"""

from __future__ import annotations

from typing import Any

# Keys written by the CV tab (prefix cv_ws_ for workspace-scoped data)
KEY_VERSION = "cv_workspace_version"
KEY_ANALYSIS_READY = "cv_analysis_ready"
KEY_STRUCTURED = "cv_structured_extraction_dict"
KEY_BUNDLE = "cv_last_bundle_dict"
KEY_EXPORT = "cv_export_payload"
KEY_FILE_HASH = "cv_file_hash"
KEY_FILE_META = "cv_file_meta"
KEY_DEBUG_RAW_LEN = "cv_debug_raw_len"
KEY_DEBUG_CLEAN = "cv_debug_clean_preview"
KEY_LAST_ERROR = "cv_last_error"
# Workspace mode: which generation output is authoritative for the UI ("none" | "practice" | "full_prep").
KEY_ACTIVE_MODE = "cv_active_mode"
KEY_PRACTICE_BUNDLE = "cv_practice_bundle_dict"
KEY_PRACTICE_ANSWERS = "cv_practice_answers_dict"
KEY_PRACTICE_EVAL_BATCH = "cv_practice_evaluation_batch_dict"
KEY_PRACTICE_EVAL_ERROR = "cv_practice_eval_last_error"

_ALL_KEYS: tuple[str, ...] = (
    KEY_ANALYSIS_READY,
    KEY_STRUCTURED,
    KEY_BUNDLE,
    KEY_EXPORT,
    KEY_FILE_HASH,
    KEY_FILE_META,
    KEY_DEBUG_RAW_LEN,
    KEY_DEBUG_CLEAN,
    KEY_LAST_ERROR,
    KEY_ACTIVE_MODE,
    KEY_PRACTICE_BUNDLE,
    KEY_PRACTICE_ANSWERS,
    KEY_PRACTICE_EVAL_BATCH,
    KEY_PRACTICE_EVAL_ERROR,
)


def get_cv_workspace_version(session_state: dict[str, Any]) -> int:
    """Uploader widget key suffix; bump on reset to clear the file input."""
    v = session_state.get(KEY_VERSION)
    return int(v) if v is not None else 0


def bump_cv_workspace_version(session_state: dict[str, Any]) -> int:
    """Increment version so Streamlit remounts the file uploader with a fresh key."""
    n = get_cv_workspace_version(session_state) + 1
    session_state[KEY_VERSION] = n
    return n


def clear_cv_results_and_errors(session_state: dict[str, Any]) -> None:
    """Clear displayed results, export payload, and last error (keep analysis_ready / extraction if any)."""
    for k in (
        KEY_BUNDLE,
        KEY_EXPORT,
        KEY_LAST_ERROR,
        KEY_ACTIVE_MODE,
        KEY_PRACTICE_BUNDLE,
        KEY_PRACTICE_ANSWERS,
        KEY_PRACTICE_EVAL_BATCH,
        KEY_PRACTICE_EVAL_ERROR,
    ):
        session_state.pop(k, None)


def clear_cv_workspace(session_state: dict[str, Any]) -> int:
    """
    Full reset: analysis state, file metadata, errors, and bump uploader version.

    Returns:
        New workspace version number.
    """
    for k in _ALL_KEYS:
        session_state.pop(k, None)
    return bump_cv_workspace_version(session_state)


def analysis_ready(session_state: dict[str, Any]) -> bool:
    """True after a successful full analyze (structured CV stored)."""
    return bool(session_state.get(KEY_ANALYSIS_READY))


def on_full_analyze_failure(session_state: dict[str, Any]) -> None:
    """Full analyze failed: remove prior success artifacts so the UI does not show stale output."""
    session_state[KEY_ANALYSIS_READY] = False
    session_state.pop(KEY_STRUCTURED, None)
    session_state.pop(KEY_BUNDLE, None)
    session_state.pop(KEY_EXPORT, None)
    session_state.pop(KEY_FILE_HASH, None)
    session_state.pop(KEY_FILE_META, None)
    session_state.pop(KEY_DEBUG_RAW_LEN, None)
    session_state.pop(KEY_DEBUG_CLEAN, None)
    session_state.pop(KEY_ACTIVE_MODE, None)
    session_state.pop(KEY_PRACTICE_BUNDLE, None)
    session_state.pop(KEY_PRACTICE_ANSWERS, None)
    session_state.pop(KEY_PRACTICE_EVAL_BATCH, None)
    session_state.pop(KEY_PRACTICE_EVAL_ERROR, None)


def on_regenerate_failure(session_state: dict[str, Any]) -> None:
    """Full prep regenerate failed: drop generated bundle only; keep structured CV for retry."""
    session_state.pop(KEY_BUNDLE, None)
    session_state.pop(KEY_EXPORT, None)


def on_practice_regenerate_failure(session_state: dict[str, Any]) -> None:
    """Practice question regenerate failed; keep structured CV for retry."""
    session_state.pop(KEY_PRACTICE_BUNDLE, None)
    session_state.pop(KEY_PRACTICE_EVAL_BATCH, None)
    session_state.pop(KEY_PRACTICE_EVAL_ERROR, None)


def on_full_analyze_success(session_state: dict[str, Any]) -> None:
    session_state[KEY_LAST_ERROR] = None
    session_state[KEY_ANALYSIS_READY] = True


def on_regenerate_success(session_state: dict[str, Any]) -> None:
    session_state[KEY_LAST_ERROR] = None
