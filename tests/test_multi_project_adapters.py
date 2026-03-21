from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.state import OrchestratorState


@dataclass
class _ConfigWrapper:
    config: Any


class _StubBacklogTracker:
    def scan_tasks(self):
        return []

    def load_state(self, path):
        return []

    def save_state(self, path, tasks):
        return None

    def get_next_task(self, tasks):
        return None


class _StubTask:
    def __init__(self, name: str = "001_task.py", order: int = 1, status: str = "pending") -> None:
        self.name = name
        self.order = order
        self.status = status


def _make_runner(config) -> OrchestratorRunner:
    return OrchestratorRunner(_ConfigWrapper(config=config), _StubBacklogTracker(), OrchestratorState(tasks=[]))


def _generic_config_fields(config) -> tuple[str, str, str, str, str]:
    return (
        config.tasks_directory,
        config.branch_naming_pattern,
        config.task_file_pattern,
        config.lint_command,
        config.test_command,
    )


def test_tradingbot_default_config_factory_returns_usable_config() -> None:
    config = ProjectAdapter.get_tradingbot_default_config()

    assert isinstance(config.tasks_directory, str)
    assert config.tasks_directory == "tasks/"
    assert config.branch_naming_pattern == "feature/*"
    assert config.task_file_pattern == "*.md"
    assert config.lint_command == "ruff check ."
    assert config.test_command == "pytest -q"
    assert config.task_runner_command is None


def test_generic_project_config_factory_returns_distinct_usable_config() -> None:
    tradingbot = ProjectAdapter.get_tradingbot_default_config()
    generic = ProjectAdapter.get_generic_project_config()

    assert isinstance(generic.tasks_directory, str)
    assert generic.tasks_directory != tradingbot.tasks_directory
    assert generic.branch_naming_pattern != tradingbot.branch_naming_pattern
    assert generic.task_file_pattern != tradingbot.task_file_pattern
    assert generic.lint_command != tradingbot.lint_command
    assert generic.test_command != tradingbot.test_command

    for field in _generic_config_fields(generic):
        assert isinstance(field, str)
        assert field != ""


def test_runner_can_be_constructed_with_tradingbot_config() -> None:
    config = ProjectAdapter.get_tradingbot_default_config()
    runner = _make_runner(config)

    assert runner.config.tasks_directory == config.tasks_directory
    assert runner.backlog_tracker.__class__ is _StubBacklogTracker
    assert runner.state.tasks == []


def test_runner_can_be_constructed_with_generic_config() -> None:
    config = ProjectAdapter.get_generic_project_config()
    runner = _make_runner(config)

    assert runner.config.tasks_directory == config.tasks_directory
    assert runner.backlog_tracker.__class__ is _StubBacklogTracker
    assert runner.state.tasks == []


def test_run_next_task_dry_run_works_with_both_configs() -> None:
    for config in (
        ProjectAdapter.get_tradingbot_default_config(),
        ProjectAdapter.get_generic_project_config(),
    ):
        runner = _make_runner(config)
        runner.backlog_tracker.scan_tasks = lambda: [_StubTask()]
        runner.backlog_tracker.get_next_task = lambda tasks: tasks[0]

        result = runner.run_next_task(dry_run=True)

        assert result["dry_run"] is True
        assert result["task_name"] == "001_task.py"
        assert result["status"] == "planned"
        assert result["message"] == "Task is planned for execution."
        assert result["outcome"] == "noop"
        assert result["next_action"] == "none"
        assert result["requires_approval"] is False


def test_run_loop_max_tasks_one_uses_current_baseline_for_both_configs() -> None:
    for config in (
        ProjectAdapter.get_tradingbot_default_config(),
        ProjectAdapter.get_generic_project_config(),
    ):
        runner = _make_runner(config)

        with patch.object(
            runner,
            "run_next_task",
            side_effect=[
                {
                    "task_name": "001_task.py",
                    "status": "running",
                    "message": "Task is now running.",
                    "outcome": "ready_for_pr",
                    "next_action": "merge",
                    "requires_approval": False,
                }
            ],
        ):
            result = runner.run_loop(max_tasks=1)

        assert result["processed_tasks"] == ["001_task.py"]
        assert result["stopped_reason"] == "Reached max_tasks limit of 1"
        assert result["final_status"] == "running"
        assert result["approval_required"] is False
        assert result["planned_actions"] == ["Task 001_task.py completed successfully."]


def test_generic_config_is_usable_without_tradingbot_only_assumptions() -> None:
    config = ProjectAdapter.get_generic_project_config()
    runner = _make_runner(config)

    runner.backlog_tracker.scan_tasks = lambda: [_StubTask(name="alpha.task", order=7, status="pending")]
    runner.backlog_tracker.get_next_task = lambda tasks: tasks[0]

    result = runner.run_next_task(dry_run=True)

    assert result["task_name"] == "alpha.task"
    assert result["status"] == "planned"
    assert result["message"] == "Task is planned for execution."
    assert Path(config.tasks_directory).name == Path(config.tasks_directory).name
