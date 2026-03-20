from pathlib import Path

from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.project_adapter import ProjectConfig
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.state import OrchestratorState, TaskMetadata, TaskStatus


def task(name: str, order: int) -> TaskMetadata:
    return TaskMetadata(name=name, order=order, status=TaskStatus(status="pending"))


def make_runner(tmp_path: Path, tasks: list[TaskMetadata]) -> OrchestratorRunner:
    config = ProjectConfig(
        tasks_directory=str(tmp_path),
        lint_command="",
        test_command="",
        branch_naming_pattern="feature/*",
        protected_file_patterns=[],
        artifact_path_patterns=[],
        approval_required_file_patterns=[],
    )
    backlog_tracker = BacklogTracker(tasks_directory=str(tmp_path))
    state = OrchestratorState(tasks=tasks)
    return OrchestratorRunner(config, backlog_tracker, state)


def test_run_loop_stops_when_backlog_completes(tmp_path: Path) -> None:
    runner = make_runner(
        tmp_path,
        [task("one.md", 1), task("two.md", 2)],
    )

    runner.run_next_task = lambda dry_run=False: {  # type: ignore[assignment]
        "task_name": "one.md",
        "status": "running",
        "message": "Task is now running.",
        "outcome": "ready_for_pr",
        "next_action": "merge",
        "requires_approval": False,
    }

    calls = {"count": 0}

    def fake_run_next_task(dry_run: bool = False) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "task_name": "one.md",
                "status": "running",
                "message": "Task is now running.",
                "outcome": "ready_for_pr",
                "next_action": "merge",
                "requires_approval": False,
            }
        return {
            "task_name": "none",
            "status": "no_task",
            "message": "No pending tasks available.",
            "outcome": "noop",
            "next_action": "none",
            "requires_approval": False,
        }

    runner.run_next_task = fake_run_next_task  # type: ignore[assignment]

    summary = runner.run_loop(max_tasks=5)

    assert calls["count"] == 2
    assert summary["processed_tasks"] == ["one.md"]
    assert summary["stopped_reason"] == "No pending tasks available."
    assert summary["final_status"] == "completed"
    assert summary["approval_required"] is False
    assert summary["planned_actions"] == ["Task one.md completed successfully."]


def test_run_loop_stops_on_failure(tmp_path: Path) -> None:
    runner = make_runner(tmp_path, [task("one.md", 1), task("two.md", 2)])

    calls = {"count": 0}

    def fake_run_next_task(dry_run: bool = False) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "task_name": "one.md",
                "status": "failed",
                "message": "Execution failed: boom",
                "outcome": "repair_required",
                "next_action": "require_human_review",
                "requires_approval": True,
            }
        return {
            "task_name": "none",
            "status": "no_task",
            "message": "No pending tasks available.",
            "outcome": "noop",
            "next_action": "none",
            "requires_approval": False,
        }

    runner.run_next_task = fake_run_next_task  # type: ignore[assignment]

    summary = runner.run_loop(max_tasks=5)

    assert calls["count"] == 1
    assert summary["processed_tasks"] == ["one.md"]
    assert summary["stopped_reason"] == "Execution failed: boom"
    assert summary["final_status"] == "failed"
    assert summary["approval_required"] is False
    assert summary["planned_actions"] == []


def test_run_loop_stops_on_approval_required(tmp_path: Path) -> None:
    runner = make_runner(tmp_path, [task("one.md", 1), task("two.md", 2)])

    calls = {"count": 0}

    def fake_run_next_task(dry_run: bool = False) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "task_name": "one.md",
                "status": "running",
                "message": "Task is now running.",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }
        return {
            "task_name": "none",
            "status": "no_task",
            "message": "No pending tasks available.",
            "outcome": "noop",
            "next_action": "none",
            "requires_approval": False,
        }

    runner.run_next_task = fake_run_next_task  # type: ignore[assignment]

    summary = runner.run_loop(max_tasks=5)

    assert calls["count"] == 1
    assert summary["processed_tasks"] == ["one.md"]
    assert summary["stopped_reason"] == "Approval required"
    assert summary["final_status"] == "blocked"
    assert summary["approval_required"] is True
    assert summary["planned_actions"] == ["Task one.md completed successfully."]


def test_run_loop_max_tasks_stops_infinite_loop(tmp_path: Path) -> None:
    runner = make_runner(tmp_path, [task("one.md", 1)])

    calls = {"count": 0}

    def fake_run_next_task(dry_run: bool = False) -> dict[str, object]:
        calls["count"] += 1
        return {
            "task_name": "one.md",
            "status": "running",
            "message": "Task is now running.",
            "outcome": "ready_for_pr",
            "next_action": "merge",
            "requires_approval": False,
        }

    runner.run_next_task = fake_run_next_task  # type: ignore[assignment]

    summary = runner.run_loop(max_tasks=3)

    assert calls["count"] == 3
    assert summary["processed_tasks"] == ["one.md", "one.md", "one.md"]
    assert summary["stopped_reason"] == "Reached max_tasks limit of 3"
    assert summary["final_status"] == "running"
    assert summary["approval_required"] is False
    assert summary["planned_actions"] == [
        "Task one.md completed successfully.",
        "Task one.md completed successfully.",
        "Task one.md completed successfully.",
    ]


def test_run_loop_does_not_count_no_task_sentinel(tmp_path: Path) -> None:
    runner = make_runner(tmp_path, [task("one.md", 1)])

    calls = {"count": 0}

    def fake_run_next_task(dry_run: bool = False) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "task_name": "one.md",
                "status": "running",
                "message": "Task is now running.",
                "outcome": "ready_for_pr",
                "next_action": "merge",
                "requires_approval": False,
            }
        return {
            "task_name": "none",
            "status": "no_task",
            "message": "No pending tasks available.",
            "outcome": "noop",
            "next_action": "none",
            "requires_approval": False,
        }

    runner.run_next_task = fake_run_next_task  # type: ignore[assignment]

    summary = runner.run_loop(max_tasks=5)

    assert summary["processed_tasks"] == ["one.md"]
    assert calls["count"] == 2
    assert summary["final_status"] == "completed"
    assert summary["stopped_reason"] == "No pending tasks available."


def test_run_loop_normal_completion_uses_completed_status(tmp_path: Path) -> None:
    runner = make_runner(tmp_path, [task("one.md", 1), task("two.md", 2)])

    calls = {"count": 0}

    def fake_run_next_task(dry_run: bool = False) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "task_name": "one.md",
                "status": "running",
                "message": "Task is now running.",
                "outcome": "ready_for_pr",
                "next_action": "merge",
                "requires_approval": False,
            }
        if calls["count"] == 2:
            return {
                "task_name": "two.md",
                "status": "running",
                "message": "Task is now running.",
                "outcome": "ready_for_pr",
                "next_action": "merge",
                "requires_approval": False,
            }
        return {
            "task_name": "none",
            "status": "no_task",
            "message": "No pending tasks available.",
            "outcome": "noop",
            "next_action": "none",
            "requires_approval": False,
        }

    runner.run_next_task = fake_run_next_task  # type: ignore[assignment]

    summary = runner.run_loop(max_tasks=5)

    assert summary["processed_tasks"] == ["one.md", "two.md"]
    assert summary["final_status"] == "completed"
    assert summary["approval_required"] is False
    assert summary["stopped_reason"] == "No pending tasks available."
    assert summary["planned_actions"] == [
        "Task one.md completed successfully.",
        "Task two.md completed successfully.",
    ]
