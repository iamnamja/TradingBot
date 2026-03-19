from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, List
from unittest.mock import patch

from builder.orchestrator.cli import main as cli_main


class _Seq:
    def __init__(self, results: List[dict[str, Any]]):
        self._results = list(results)
        self._i = 0

    def next(self) -> dict[str, Any]:
        if self._i >= len(self._results):
            return {
                "task_name": "none",
                "status": "no_task",
                "message": "No pending tasks available.",
                "outcome": "noop",
                "next_action": "none",
                "requires_approval": False,
            }
        r = self._results[self._i]
        self._i += 1
        return r


def _running_result(task_name: str, outcome: str = "ready_for_pr", next_action: str = "merge") -> dict[str, Any]:
    return {
        "task_name": task_name,
        "status": "running",
        "message": "Task is now running.",
        "outcome": outcome,
        "next_action": next_action,
        "requires_approval": False,
    }


def _approval_blocked(task_name: str) -> dict[str, Any]:
    return {
        "task_name": task_name,
        "status": "running",
        "message": "Task is now running.",
        "outcome": "review_blocked",
        "next_action": "requires_approval",
        "requires_approval": True,
    }


def _failed(task_name: str) -> dict[str, Any]:
    return {
        "task_name": task_name,
        "status": "failed",
        "message": "Boom!",
        "outcome": "repair_required",
        "next_action": "require_human_review",
        "requires_approval": False,
    }


def test_run_loop_completes_on_backlog_empty(monkeypatch, tmp_path: Path, capsys):
    seq = _Seq([_running_result("task1.py"), _running_result("task2.py")])

    def fake_run_next_task(self, dry_run: bool = False):
        return seq.next()

    sys.argv = ["prog", "run-loop", "--max-tasks", "10"]
    audit_file = tmp_path / "audit.jsonl"
    sys.argv += ["--audit-path", str(audit_file)]

    with patch("builder.orchestrator.runner.OrchestratorRunner.run_next_task", new=fake_run_next_task):
        exit_code = cli_main()
        assert exit_code == 0

    out_lines = capsys.readouterr().out.strip().splitlines()
    # Expect two iteration lines + 3 summary lines
    assert "[Task 1] task1.py — ready_for_pr (merge)" in out_lines[0]
    assert "[Task 2] task2.py — ready_for_pr (merge)" in out_lines[1]
    assert out_lines[-3].startswith("Run complete: completed")
    assert out_lines[-2].startswith("Tasks processed: 2")
    assert out_lines[-1].startswith("Stopped reason: No pending tasks")

    # Decision log entries were written (only for actual tasks, not the sentinel)
    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    entries = [json.loads(line) for line in lines]
    assert entries[0]["task_name"] == "task1.py"
    assert entries[1]["task_name"] == "task2.py"


def test_run_loop_stops_on_failure(monkeypatch, capsys):
    seq = _Seq([_running_result("task1.py"), _failed("task2.py")])

    def fake_run_next_task(self, dry_run: bool = False):
        return seq.next()

    sys.argv = ["prog", "run-loop", "--max-tasks", "10"]

    with patch("builder.orchestrator.runner.OrchestratorRunner.run_next_task", new=fake_run_next_task):
        exit_code = cli_main()
        assert exit_code == 1

    out = capsys.readouterr().out.strip().splitlines()
    assert "[Task 1] task1.py — ready_for_pr (merge)" in out[0]
    assert "[Task 2] task2.py — repair_required (require_human_review)" in out[1]
    assert out[-3].startswith("Run complete: failed")
    assert out[-1].startswith("Stopped reason: Task failed")


def test_run_loop_stops_on_approval(monkeypatch, capsys):
    seq = _Seq([_running_result("task1.py"), _approval_blocked("task2.py")])

    def fake_run_next_task(self, dry_run: bool = False):
        return seq.next()

    sys.argv = ["prog", "run-loop", "--max-tasks", "10"]

    with patch("builder.orchestrator.runner.OrchestratorRunner.run_next_task", new=fake_run_next_task):
        exit_code = cli_main()
        # Non-zero since blocked
        assert exit_code == 1

    out = capsys.readouterr().out.strip().splitlines()
    assert "[Task 1] task1.py — ready_for_pr (merge)" in out[0]
    assert "[Task 2] task2.py — review_blocked (requires_approval)" in out[1]
    assert out[-3].startswith("Run complete: blocked")
    assert out[-1].startswith("Stopped reason: Approval required")


def test_run_loop_respects_max_tasks(monkeypatch, capsys):
    # Three running results but max-tasks=2 should stop earlier
    seq = _Seq([_running_result("a.py"), _running_result("b.py"), _running_result("c.py")])

    def fake_run_next_task(self, dry_run: bool = False):
        return seq.next()

    sys.argv = ["prog", "run-loop", "--max-tasks", "2"]

    with patch("builder.orchestrator.runner.OrchestratorRunner.run_next_task", new=fake_run_next_task):
        exit_code = cli_main()
        assert exit_code == 1  # incomplete

    out_lines = capsys.readouterr().out.strip().splitlines()
    # Should print only two iterations due to max-tasks=2, then summary
    task_lines = [line for line in out_lines if line.startswith("[Task ")]
    assert len(task_lines) == 2
    assert out_lines[-3].startswith("Run complete: incomplete")
    assert out_lines[-1].startswith("Stopped reason: Max tasks reached")


def test_simulate_mode(monkeypatch, capsys):
    # Ensure simulate subcommand runs without invoking real execution
    sys.argv = ["prog", "simulate"]
    exit_code = cli_main()
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Processed Tasks:" in out
    assert "Final Status:" in out


def test_run_loop_no_audit_path(monkeypatch, capsys):
    seq = _Seq([_running_result("foo.py")])

    def fake_run_next_task(self, dry_run: bool = False):
        return seq.next()

    sys.argv = ["prog", "run-loop", "--max-tasks", "5"]

    with patch("builder.orchestrator.runner.OrchestratorRunner.run_next_task", new=fake_run_next_task):
        exit_code = cli_main()
        assert exit_code == 0

    out = capsys.readouterr().out.strip().splitlines()
    assert "[Task 1] foo.py — ready_for_pr (merge)" in out[0]
