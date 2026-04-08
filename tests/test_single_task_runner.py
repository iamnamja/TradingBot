from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


def _load_single_task_modules():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    run_single_task = importlib.import_module("agents.run_single_task")
    run_task = importlib.import_module("agents.run_task")
    return run_single_task, run_task


def test_single_task_runner_blocks_escalation_first_work_without_execution(tmp_path) -> None:
    run_single_task, _ = _load_single_task_modules()
    task_path = tmp_path / "task_139_control_plane.md"
    task_path.write_text(
        """
# Task 139 — Control-plane change

## Create or update these exact files
- `agents/run_task.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
""".strip(),
        encoding="utf-8",
    )
    ledger_path = tmp_path / "ledger.jsonl"
    executed: list[list[str]] = []

    def fake_executor(command):
        executed.append(list(command))
        return {"command": list(command), "returncode": 0, "stdout": "", "stderr": ""}

    result = run_single_task.run_autonomous_single_task(
        task_path.as_posix(),
        ledger_path=ledger_path,
        executor=fake_executor,
        now=lambda: "2026-04-08T17:40:00Z",
    )

    assert executed == []
    entry = dict(result["entry"])
    assert entry["final_decision"] == "escalation_required"
    assert entry["admission"]["autonomous_single_task_lane"] == "escalation_required"
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    persisted = json.loads(lines[0])
    assert persisted["escalation"]["required"] is True
    assert persisted["validation"]["execution_invoked"] is False


def test_single_task_runner_executes_admitted_safe_task_and_persists_ledger(tmp_path) -> None:
    run_single_task, _ = _load_single_task_modules()
    task_path = tmp_path / "task_139_safe.md"
    task_path.write_text(
        """
# Task 139 — Safe docs and tests change

## Create or update these exact files
- `tests/test_single_task_runner.py`
- `tests/test_run_task_runtime_foundations.py`
""".strip(),
        encoding="utf-8",
    )
    ledger_path = tmp_path / "ledger.jsonl"

    def fake_executor(command):
        return {
            "command": list(command),
            "returncode": 0,
            "stdout": """
=== Iteration 1/4 ===
=== Iteration 2/4 ===
All checks passed!
........................................................................ [100%]
last-known-good subset preserved during retry
""".strip(),
            "stderr": "",
        }

    result = run_single_task.run_autonomous_single_task(
        task_path.as_posix(),
        provider="openai",
        model="gpt-5.4",
        max_iters=4,
        ledger_path=ledger_path,
        executor=fake_executor,
        now=lambda: "2026-04-08T17:41:00Z",
    )

    entry = dict(result["entry"])
    assert entry["final_decision"] == "completed"
    assert entry["admission"]["autonomous_single_task_lane"] == "autonomous_safe"
    assert entry["retry"]["retry_count_observed"] == 1
    assert entry["retry"]["last_green_subset_preserved_observed"] is True
    assert entry["validation"]["all_checks_passed_observed"] is True
    assert entry["validation"]["pytest_green_observed"] is True
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    persisted = json.loads(lines[0])
    assert persisted["execution"]["command"][0]
    assert persisted["push_requested"] is False


def test_run_task_wrappers_delegate_to_single_task_runner(tmp_path) -> None:
    _, run_task = _load_single_task_modules()
    task_path = tmp_path / "task_139_safe_wrappers.md"
    task_path.write_text(
        """
# Task 139 — Safe docs change

## Create or update these exact files
- `tests/test_single_task_runner.py`
""".strip(),
        encoding="utf-8",
    )
    ledger_path = tmp_path / "ledger.jsonl"

    def fake_executor(command):
        return {
            "command": list(command),
            "returncode": 0,
            "stdout": "=== Iteration 1/4 ===\nAll checks passed!\n................................ [100%]",
            "stderr": "",
        }

    result = run_task.run_autonomous_single_task(
        task_path.as_posix(),
        ledger_path=ledger_path,
        executor=fake_executor,
        now=lambda: "2026-04-08T17:42:00Z",
    )

    assert run_task.default_single_task_ledger_path().endswith("run_ledger.jsonl")
    assert result["entry"]["final_decision"] == "completed"
    assert ledger_path.exists()
