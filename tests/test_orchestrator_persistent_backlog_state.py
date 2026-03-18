from __future__ import annotations

from pathlib import Path

import pytest

from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.state import OrchestratorState



def _write_task(tasks_dir: Path, order: int, stem: str) -> Path:
    task_path = tasks_dir / f"{order:03d}_{stem}.py"
    task_path.write_text("print('task')\n", encoding="utf-8")
    return task_path


@pytest.fixture
def tasks_dir(tmp_path: Path) -> Path:
    path = tmp_path / "tasks"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def config(tasks_dir: Path):
    config = ProjectAdapter.get_tradingbot_default_config()
    config.tasks_directory = str(tasks_dir)
    config.state_path = str(tasks_dir / "state.json")
    return config


@pytest.fixture
def runner(config):
    tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    runner = OrchestratorRunner(
        config=config,
        backlog_tracker=tracker,
        initial_state=OrchestratorState(tasks=[]),
    )
    runner.skip_guardrails = True
    return runner


def test_state_file_created_and_completed_task_persisted(runner, tasks_dir: Path, config):
    _write_task(tasks_dir, 1, "first")

    result = runner.run_next_task(dry_run=False)

    assert result["task_name"] == "first.py"
    assert result["status"] == "running"
    assert result["message"] == "Task is now running."
    assert result["outcome"] == "ready_for_pr"
    assert Path(config.state_path).exists()

    state = OrchestratorState.load(config.state_path)
    assert len(state.tasks) == 1
    assert state.tasks[0].name == "first.py"
    assert state.tasks[0].order == 1
    assert state.tasks[0].status.status == "completed"


def test_completed_tasks_are_skipped_on_next_run(tasks_dir: Path, config):
    _write_task(tasks_dir, 1, "first")
    _write_task(tasks_dir, 2, "second")

    tracker = BacklogTracker(tasks_directory=config.tasks_directory)

    first_runner = OrchestratorRunner(
        config=config,
        backlog_tracker=tracker,
        initial_state=OrchestratorState(tasks=[]),
    )
    first_runner.skip_guardrails = True
    first_result = first_runner.run_next_task(dry_run=False)

    second_runner = OrchestratorRunner(
        config=config,
        backlog_tracker=tracker,
        initial_state=OrchestratorState(tasks=[]),
    )
    second_runner.skip_guardrails = True
    second_result = second_runner.run_next_task(dry_run=False)

    assert first_result["task_name"] == "first.py"
    assert second_result["task_name"] == "second.py"
    assert second_result["status"] == "running"
    assert second_result["outcome"] == "ready_for_pr"

    state = OrchestratorState.load(config.state_path)
    assert [task.name for task in state.tasks] == ["first.py", "second.py"]
    assert [task.status.status for task in state.tasks] == ["completed", "completed"]


def test_failed_task_is_persisted_after_real_run(tasks_dir: Path, config):
    _write_task(tasks_dir, 1, "first")

    tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    failing_runner = OrchestratorRunner(
        config=config,
        backlog_tracker=tracker,
        initial_state=OrchestratorState(tasks=[]),
    )
    failing_runner.skip_guardrails = True
    failing_runner.execute_task = lambda task: {
        "success": False,
        "failure_text": "Execution failed",
        "changed_files": [],
    }

    result = failing_runner.run_next_task(dry_run=False)

    assert result["task_name"] == "first.py"
    assert result["status"] == "failed"
    assert result["outcome"] == "repair_required"

    state = OrchestratorState.load(config.state_path)
    assert len(state.tasks) == 1
    assert state.tasks[0].name == "first.py"
    assert state.tasks[0].status.status == "failed"


def test_fresh_runner_picks_up_persisted_state(tasks_dir: Path, config):
    _write_task(tasks_dir, 1, "first")
    _write_task(tasks_dir, 2, "second")

    tracker = BacklogTracker(tasks_directory=config.tasks_directory)

    first_runner = OrchestratorRunner(
        config=config,
        backlog_tracker=tracker,
        initial_state=OrchestratorState(tasks=[]),
    )
    first_runner.skip_guardrails = True
    first_runner.run_next_task(dry_run=False)

    fresh_runner = OrchestratorRunner(
        config=config,
        backlog_tracker=tracker,
        initial_state=OrchestratorState(tasks=[]),
    )
    fresh_runner.skip_guardrails = True
    result = fresh_runner.run_next_task(dry_run=False)

    assert result["task_name"] == "second.py"
    assert result["status"] == "running"
    assert result["outcome"] == "ready_for_pr"

    state = OrchestratorState.load(config.state_path)
    assert [task.name for task in state.tasks] == ["first.py", "second.py"]
