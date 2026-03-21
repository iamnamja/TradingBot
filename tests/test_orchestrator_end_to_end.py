from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.state import OrchestratorState


class _ConfigWrapper:
    def __init__(self) -> None:
        self.config = SimpleNamespace(
            tasks_directory=Path("tasks"),
            state_path=Path("state.json"),
            approval_required_file_patterns=["*"],
            protected_file_patterns=["*"],
            task_runner_command=["python", "-m", "builder.orchestrator.runner"],
            audit_path=Path("audit.log"),
        )


class _StubBacklogTracker:
    def scan_tasks(self):
        return []

    def load_state(self, path):
        return []

    def save_state(self, path, tasks):
        return None

    def get_next_task(self, tasks):
        return None


class _Task:
    def __init__(self, name: str, order: int = 1, status: str = "pending") -> None:
        self.name = name
        self.order = order
        self.status = status


def _make_runner() -> OrchestratorRunner:
    return OrchestratorRunner(_ConfigWrapper(), _StubBacklogTracker(), OrchestratorState(tasks=[]))


def test_run_loop_full_success_path() -> None:
    runner = _make_runner()
    with patch.object(
        runner,
        "run_next_task",
        side_effect=[
            {
                "task_name": "001_task.py",
                "status": "running",
                "message": "Task executed successfully.",
                "outcome": "ready_for_pr",
                "next_action": "continue",
                "requires_approval": False,
            },
            {
                "task_name": "002_task.py",
                "status": "running",
                "message": "Task executed successfully.",
                "outcome": "ready_for_pr",
                "next_action": "continue",
                "requires_approval": False,
            },
            {
                "task_name": "none",
                "status": "no_task",
                "message": "No pending tasks available.",
                "outcome": "noop",
                "next_action": "none",
                "requires_approval": False,
            },
        ],
    ):
        result = runner.run_loop()

    assert result["processed_tasks"] == ["001_task.py", "002_task.py"]
    assert result["final_status"] == "completed"
    assert result["approval_required"] is False
    assert result["stopped_reason"] == "No pending tasks available."
    assert result["planned_actions"] == [
        "Task 001_task.py completed successfully.",
        "Task 002_task.py completed successfully.",
    ]


def test_run_loop_execution_failure_stops_the_loop() -> None:
    runner = _make_runner()
    with patch.object(
        runner,
        "run_next_task",
        side_effect=[
            {
                "task_name": "001_task.py",
                "status": "failed",
                "message": "Execution failed.",
                "outcome": "failed",
                "next_action": "stop",
                "requires_approval": False,
            }
        ],
    ):
        result = runner.run_loop()

    assert result["processed_tasks"] == ["001_task.py"]
    assert result["final_status"] == "failed"
    assert result["approval_required"] is False
    assert result["stopped_reason"] == "Execution failed."
    assert result["planned_actions"] == []


def test_run_loop_approval_checkpoint_blocks_run() -> None:
    runner = _make_runner()
    with patch.object(
        runner,
        "run_next_task",
        side_effect=[
            {
                "task_name": "001_task.py",
                "status": "running",
                "message": "Task executed successfully.",
                "outcome": "ready_for_pr",
                "next_action": "continue",
                "requires_approval": False,
            },
            {
                "task_name": "002_task.py",
                "status": "running",
                "message": "Approval required.",
                "outcome": "ready_for_pr",
                "next_action": "continue",
                "requires_approval": True,
            },
        ],
    ):
        result = runner.run_loop()

    assert result["processed_tasks"] == ["001_task.py", "002_task.py"]
    assert result["approval_required"] is True
    assert result["final_status"] == "blocked"
    assert result["stopped_reason"] == "Approval required"
    assert result["planned_actions"] == [
        "Task 001_task.py completed successfully.",
        "Task 002_task.py completed successfully.",
    ]


def test_run_next_task_empty_backlog_returns_no_task() -> None:
    runner = _make_runner()
    with patch.object(runner.backlog_tracker, "load_state", return_value=[]):
        result = runner.run_next_task()

    assert result["status"] == "no_task"
    assert result["task_name"] == "none"


def test_run_next_task_dry_run_plans_first_task_without_executing() -> None:
    runner = _make_runner()
    with patch.object(
        runner.backlog_tracker,
        "load_state",
        return_value=[_Task("001_task.py")],
    ):
        with patch.object(runner.backlog_tracker, "get_next_task", return_value=_Task("001_task.py")):
            result = runner.run_next_task(dry_run=True)

    assert result["status"] == "planned"
    assert result["task_name"] == "001_task.py"
