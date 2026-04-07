from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _bootstrap_repo_root() -> None:
    repo_root = _repo_root()
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _load_failure_journal_module():
    _bootstrap_repo_root()
    if "agents.lib.failure_journal" in sys.modules:
        del sys.modules["agents.lib.failure_journal"]
    return importlib.import_module("agents.lib.failure_journal")


def _load_run_task_module():
    _bootstrap_repo_root()
    if "agents.run_task" in sys.modules:
        del sys.modules["agents.run_task"]
    return importlib.import_module("agents.run_task")

def test_failure_journal_live_seam_exports_are_stable_and_do_not_require_module_alias() -> None:
    run_task = _load_run_task_module()
    exports = run_task._failure_journal_exports()

    expected_keys = {
        "failure_journal",
        "classify_failure",
        "failure_fingerprint",
        "bounded_failure_snippet",
        "recommended_next_action",
        "chosen_remediation_path",
        "append_failure_journal_entry",
        "retry_count_for_fingerprint",
        "build_failure_remediation_plan",
        "autonomy_confidence",
        "continue_autonomously",
        "choose_repair_strategy",
        "build_repair_attempt_record",
        "repair_attempt_fingerprint",
        "evaluate_repair_attempt_memory",
    }

    assert expected_keys.issubset(exports.keys())
    assert "module" not in exports
    assert exports["failure_journal"] is not None
    assert callable(exports["append_failure_journal_entry"])
    assert callable(exports["build_failure_remediation_plan"])



def test_repeated_failures_are_fingerprinted_and_counted() -> None:
    fj = _load_failure_journal_module()
    fp1 = fj.failure_fingerprint(kind="imports", message="NameError: name 'x1' is not defined", category="imports")
    fp2 = fj.failure_fingerprint(kind="imports", message="NameError: name 'x2' is not defined", category="imports")
    assert fp1 == fp2

    fj._FAILURE_COUNTS.clear()
    assert fj.retry_count_for_fingerprint(fp1) == 1
    assert fj.retry_count_for_fingerprint(fp1) == 2


def test_raw_failure_snippet_is_bounded_and_transport_safe_in_test_source() -> None:
    fj = _load_failure_journal_module()
    marker_text = (
        "prefix\n"
        + "BEGIN_" + "FILE_BUNDLE\n"
        + "FI" + "LE: x.py\n"
        + "END_" + "FILE\n"
        + "END_" + "FILE_BUNDLE\n"
    ) * 40
    bounded = fj.bounded_failure_snippet(marker_text, max_chars=120)
    assert len(bounded) <= 120
    assert "BEGIN_" + "FILE_BUNDLE" in bounded
    assert "FI" + "LE:" in bounded


def test_report_failure_delegates_through_live_export_seam(monkeypatch) -> None:
    run_task = _load_run_task_module()
    monkeypatch.setattr(run_task, "_FAILURE_JOURNAL_STATE", {}, raising=False)

    calls = {"classify": 0, "append": 0}
    entries = []

    def classify(kind, message):
        calls["classify"] += 1
        return "classified"

    def fingerprint(*, kind, message, category):
        assert category == "classified"
        return "fp-1"

    def bounded(message, max_chars=400):
        return "snippet"

    def recommend(*, kind, message, category, retry_count, fingerprint, raw_failure_snippet):
        return "retry_with_targeted_fix"

    def choose(*, kind, message, category, retry_count, fingerprint, raw_failure_snippet, recommended_next_action):
        return "retry_with_targeted_fix"

    def append(entry):
        calls["append"] += 1
        entries.append(entry)

    monkeypatch.setattr(
        run_task,
        "_failure_journal_exports",
        lambda: {
            "classify_failure": classify,
            "failure_fingerprint": fingerprint,
            "bounded_failure_snippet": bounded,
            "recommended_next_action": recommend,
            "chosen_remediation_path": choose,
            "append_failure_journal_entry": append,
            "retry_count_for_fingerprint": lambda fingerprint: 2,
        },
    )

    run_task._report_failure("imports", "boom")
    assert calls == {"classify": 1, "append": 1}
    assert entries[0]["failure_category"] == "classified"
    assert entries[0]["retry_count"] == 2
    assert entries[0]["recommended_next_action"] == "retry_with_targeted_fix"
    assert entries[0]["chosen_remediation_path"] == "retry_with_targeted_fix"


def test_report_failure_appends_journal_rows_with_recommended_and_chosen_paths(monkeypatch, tmp_path: Path) -> None:
    journal_path = tmp_path / "failure_journal.jsonl"
    monkeypatch.setenv("TRADINGBOT_FAILURE_JOURNAL_PATH", str(journal_path))
