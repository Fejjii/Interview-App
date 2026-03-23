from __future__ import annotations

from interview_app.app import cv_session_state as cvs


def test_clear_cv_workspace_resets_keys_and_bumps_version() -> None:
    ss: dict = {
        cvs.KEY_VERSION: 2,
        cvs.KEY_ANALYSIS_READY: True,
        cvs.KEY_STRUCTURED: {"profile_summary": "x"},
        cvs.KEY_BUNDLE: {"structured_extraction": {}, "generation": {}},
        cvs.KEY_EXPORT: {},
        cvs.KEY_FILE_HASH: "abc",
        cvs.KEY_LAST_ERROR: "oops",
        cvs.KEY_ACTIVE_MODE: "practice",
        cvs.KEY_PRACTICE_BUNDLE: {"x": 1},
        cvs.KEY_PRACTICE_ANSWERS: {"0": "a"},
        cvs.KEY_PRACTICE_EVAL_BATCH: {"evaluations": []},
        cvs.KEY_PRACTICE_EVAL_ERROR: "bad eval",
    }
    v = cvs.clear_cv_workspace(ss)
    assert v == 3
    assert cvs.KEY_STRUCTURED not in ss
    assert cvs.KEY_BUNDLE not in ss
    assert cvs.KEY_ANALYSIS_READY not in ss
    assert cvs.KEY_ACTIVE_MODE not in ss
    assert cvs.KEY_PRACTICE_BUNDLE not in ss
    assert cvs.KEY_PRACTICE_ANSWERS not in ss
    assert cvs.KEY_PRACTICE_EVAL_BATCH not in ss
    assert cvs.KEY_PRACTICE_EVAL_ERROR not in ss
    assert ss[cvs.KEY_VERSION] == 3


def test_on_full_analyze_failure_clears_success_artifacts() -> None:
    ss: dict = {
        cvs.KEY_ANALYSIS_READY: True,
        cvs.KEY_STRUCTURED: {"a": 1},
        cvs.KEY_BUNDLE: {"b": 2},
        cvs.KEY_EXPORT: {},
    }
    cvs.on_full_analyze_failure(ss)
    assert ss.get(cvs.KEY_ANALYSIS_READY) is False
    assert cvs.KEY_STRUCTURED not in ss
    assert cvs.KEY_BUNDLE not in ss


def test_on_practice_regenerate_failure_drops_practice_only() -> None:
    ss: dict = {
        cvs.KEY_ANALYSIS_READY: True,
        cvs.KEY_STRUCTURED: {"profile_summary": "p"},
        cvs.KEY_PRACTICE_BUNDLE: {"a": 1},
        cvs.KEY_PRACTICE_EVAL_BATCH: {"evaluations": []},
    }
    cvs.on_practice_regenerate_failure(ss)
    assert ss[cvs.KEY_STRUCTURED] == {"profile_summary": "p"}
    assert cvs.KEY_PRACTICE_BUNDLE not in ss
    assert cvs.KEY_PRACTICE_EVAL_BATCH not in ss


def test_on_regenerate_failure_keeps_structured() -> None:
    ss: dict = {
        cvs.KEY_ANALYSIS_READY: True,
        cvs.KEY_STRUCTURED: {"profile_summary": "p"},
        cvs.KEY_BUNDLE: {"x": 1},
        cvs.KEY_EXPORT: {},
    }
    cvs.on_regenerate_failure(ss)
    assert ss[cvs.KEY_STRUCTURED] == {"profile_summary": "p"}
    assert ss.get(cvs.KEY_ANALYSIS_READY) is True
    assert cvs.KEY_BUNDLE not in ss


def test_analysis_ready_requires_flag() -> None:
    assert cvs.analysis_ready({}) is False
    assert cvs.analysis_ready({cvs.KEY_ANALYSIS_READY: True}) is True


def test_get_cv_workspace_version_default() -> None:
    assert cvs.get_cv_workspace_version({}) == 0
