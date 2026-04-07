from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import pytest

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agents.lib import multi_agent_contract  # noqa: E402
from agents.lib import project_registry  # noqa: E402
from agents.lib.multi_agent_loop import execute_multi_agent_loop  # noqa: E402


def _builder_exports():
    ProjectAdapter = pytest.importorskip('builder.orchestrator.project_adapter').ProjectAdapter
    OrchestratorRunner = pytest.importorskip('builder.orchestrator.runner').OrchestratorRunner
    OrchestratorState = pytest.importorskip('builder.orchestrator.state').OrchestratorState
    return ProjectAdapter, OrchestratorRunner, OrchestratorState


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
    def __init__(self, name: str = '001_task.py', order: int = 1, status: str = 'pending') -> None:
        self.name = name
        self.order = order
        self.status = status


def _make_runner(config):
    _, OrchestratorRunner, OrchestratorState = _builder_exports()
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
    ProjectAdapter, _, _ = _builder_exports()
    config = ProjectAdapter.get_tradingbot_default_config()

    assert isinstance(config.tasks_directory, str)
    assert config.tasks_directory == 'tasks/'
    assert config.branch_naming_pattern == 'feature/*'
    assert config.task_file_pattern == '*.md'
    assert config.lint_command == 'ruff check .'
    assert config.test_command == 'pytest -q'
    assert config.task_runner_command is None


def test_generic_project_config_factory_returns_distinct_usable_config() -> None:
    ProjectAdapter, _, _ = _builder_exports()
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
        assert field != ''


def test_runner_can_be_constructed_with_tradingbot_config() -> None:
    ProjectAdapter, _, _ = _builder_exports()
    config = ProjectAdapter.get_tradingbot_default_config()
    runner = _make_runner(config)

    assert runner.config.tasks_directory == config.tasks_directory
    assert runner.backlog_tracker.__class__ is _StubBacklogTracker
    assert runner.state.tasks == []


def test_runner_can_be_constructed_with_generic_config() -> None:
    ProjectAdapter, _, _ = _builder_exports()
    config = ProjectAdapter.get_generic_project_config()
    runner = _make_runner(config)

    assert runner.config.tasks_directory == config.tasks_directory
    assert runner.backlog_tracker.__class__ is _StubBacklogTracker
    assert runner.state.tasks == []


def test_run_next_task_dry_run_works_with_both_configs() -> None:
    ProjectAdapter, _, _ = _builder_exports()
    for config in (
        ProjectAdapter.get_tradingbot_default_config(),
        ProjectAdapter.get_generic_project_config(),
    ):
        runner = _make_runner(config)
        runner.backlog_tracker.scan_tasks = lambda: [_StubTask()]
        runner.backlog_tracker.get_next_task = lambda tasks: tasks[0]

        result = runner.run_next_task(dry_run=True)

        assert result['dry_run'] is True
        assert result['task_name'] == '001_task.py'
        assert result['status'] == 'planned'
        assert result['message'] == 'Task is planned for execution.'
        assert result['outcome'] == 'noop'
        assert result['next_action'] == 'none'


def test_supervised_ordinary_manifest_reproof_is_local_first_and_truthful() -> None:
    snapshot = multi_agent_contract.multi_agent_contract_snapshot()
    assert "roles" in snapshot
    assert set(snapshot["roles"]) >= {"builder", "verifier", "controller"}

    decision = execute_multi_agent_loop(
        task_text="Short ordinary task.",
        task_path="tasks/201.md",
        max_rounds=1,
    )
    assert decision["mode"] == "supervised_local_first"
    assert decision["task_path"] == "tasks/201.md"
    assert decision["rounds_run"] == 1
    assert decision["authority_satisfied"] in {True, False}


def test_project_registry_resolves_monorepo_and_generic_external_contracts() -> None:
    snapshot = project_registry.project_registry_snapshot()
    assert set(snapshot["registered_project_ids"]) >= {"tradingbot_monorepo", "generic_python_external"}

    tradingbot = project_registry.resolve_project_contract("tradingbot_monorepo")
    generic = project_registry.resolve_project_contract("generic_python_external")

    assert tradingbot["workspace_type"] == "monorepo_python"
    assert generic["workspace_type"] == "external_python"
    assert tradingbot["allow_unattended_execution"] is False
    assert generic["allow_unattended_execution"] is False
