from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any
from unittest.mock import patch

import pytest

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agents.lib import project_workspace_adapter  # noqa: E402
from agents.lib import multi_agent_contract  # noqa: E402
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
        assert result['requires_approval'] is False


def test_run_loop_max_tasks_one_uses_current_baseline_for_both_configs() -> None:
    ProjectAdapter, _, _ = _builder_exports()
    for config in (
        ProjectAdapter.get_tradingbot_default_config(),
        ProjectAdapter.get_generic_project_config(),
    ):
        runner = _make_runner(config)

        with patch.object(
            runner,
            'run_next_task',
            side_effect=[
                {
                    'task_name': '001_task.py',
                    'status': 'running',
                    'message': 'Task is now running.',
                    'outcome': 'ready_for_pr',
                    'next_action': 'merge',
                    'requires_approval': False,
                }
            ],
        ):
            result = runner.run_loop(max_tasks=1)

        assert result['processed_tasks'] == ['001_task.py']
        assert result['stopped_reason'] == 'Reached max_tasks limit of 1'
        assert result['final_status'] == 'running'
        assert result['approval_required'] is False
        assert result['planned_actions'] == ['Task 001_task.py completed successfully.']


def test_generic_config_is_usable_without_tradingbot_only_assumptions() -> None:
    ProjectAdapter, _, _ = _builder_exports()
    config = ProjectAdapter.get_generic_project_config()
    runner = _make_runner(config)

    runner.backlog_tracker.scan_tasks = lambda: [_StubTask(name='alpha.task', order=7, status='pending')]
    runner.backlog_tracker.get_next_task = lambda tasks: tasks[0]

    result = runner.run_next_task(dry_run=True)

    assert result['task_name'] == 'alpha.task'
    assert result['status'] == 'planned'
    assert result['message'] == 'Task is planned for execution.'
    assert Path(config.tasks_directory).name == Path(config.tasks_directory).name


def test_workspace_snapshot_supports_non_tradingbot_consumers() -> None:
    snapshot = project_workspace_adapter.workspace_adapter_snapshot()

    assert snapshot['python_first_scope_only'] is True
    assert 'tradingbot' in snapshot['supported_consumers']
    assert 'generic_python' in snapshot['supported_consumers']


def test_generic_workspace_contract_is_distinct_from_tradingbot() -> None:
    tradingbot = project_workspace_adapter.tradingbot_workspace_contract('.')
    generic = project_workspace_adapter.generic_python_workspace_contract('external-app')

    assert tradingbot['consumer_name'] == 'tradingbot'
    assert generic['consumer_name'] == 'generic_python'
    assert generic['workspace_root'] == 'external-app'
    assert generic['protected_paths'] != tradingbot['protected_paths']
    assert generic['acceptance_evidence_commands'] != tradingbot['acceptance_evidence_commands']


def test_controller_can_reason_over_adapter_defined_validation_commands() -> None:
    contract = project_workspace_adapter.generic_python_workspace_contract('external-app')

    assert project_workspace_adapter.workspace_validation_commands(contract) == ['ruff check .', 'pytest -q']
    assert project_workspace_adapter.workspace_acceptance_evidence_commands(contract) == ['pytest -q']


def test_multi_agent_controller_cycle_is_portable_for_generic_python_project() -> None:
    decision_log: list[str] = []

    def _builder(role_state: dict[str, object]) -> dict[str, object]:
        task_id = str(role_state["task_path"]).split('/')[-1].split('.')[0]
        decision_log.append(f"builder:{task_id}")
        return {"changed_files": ["src/app.py"], "summary": f"builder:{task_id}"}

    def _verifier(builder_artifact: dict[str, object], _role_state: dict[str, object]) -> dict[str, object]:
        decision_log.append("verifier")
        assert builder_artifact["artifact_kind"] == "builder_patch_attempt"
        return {
            "validator_ok": True,
            "validator_note": "local validation passed",
            "focused_results": ["tests/test_multi_project_adapters.py"],
            "full_results": ["pytest -q"],
            "acceptance_report": {
                "acceptance_decision": "accepted",
                "post_task_decision": "continue",
                "next_task_may_proceed": True,
                "note": "accepted",
            },
        }

    def _controller(verifier_artifact: dict[str, object], _builder_artifact: dict[str, object], role_state: dict[str, object]) -> dict[str, object]:
        decision_log.append("controller")
        return {
            "task_path": role_state.get("task_path", "external-app/tasks/alpha.md"),
            "post_task_decision": "continue" if verifier_artifact["verdict"] == "pass" else "stop",
            "next_task_may_proceed": verifier_artifact["verdict"] == "pass",
            "summary": "verification accepted",
            "action": "advance" if verifier_artifact["verdict"] == "pass" else "stop",
        }

    manifest = [
        {"task_id": "alpha", "task_path": "external-app/tasks/alpha.md", "depends_on": []},
        {"task_id": "beta", "task_path": "external-app/tasks/beta.md", "depends_on": ["alpha"]},
    ]

    processed_task_ids: list[str] = []
    for item in manifest:
        result = execute_multi_agent_loop(
            task_path=str(item["task_path"]),
            builder_step=lambda role_state, _item=item: (processed_task_ids.append(str(_item["task_id"])) or _builder({**role_state, "task_path": str(_item["task_path"])})),
            verifier_step=_verifier,
            controller_decide=_controller,
        )
        assert result["controller_decision"]["post_task_decision"] == "continue"

    assert processed_task_ids == ["alpha", "beta"]
    assert decision_log == ["builder:alpha", "verifier", "controller", "builder:beta", "verifier", "controller"]


def test_workspace_boundary_snapshot_is_extraction_prep_not_full_extraction() -> None:
    boundary = multi_agent_contract.orchestrator_package_boundary_snapshot()

    assert boundary["product_name"] == "orchestrator"
    assert boundary["operates_inside_monorepo"] is True
    assert boundary["full_standalone_extraction_completed"] is False
    assert "tradingbot" in boundary["supported_consumers"]
    assert "generic_python" in boundary["supported_consumers"]
    assert boundary["role_contract"]["sequential_role_execution_only"] is True
    assert boundary["role_contract"]["controller_authority_over_next_role"] is True
