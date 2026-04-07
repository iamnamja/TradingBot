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

from agents import run_task  # noqa: E402
from agents.lib import multi_agent_contract  # noqa: E402
from agents.lib import project_workspace_adapter  # noqa: E402
from agents.lib.multi_agent_loop import execute_external_workspace_bootstrap_recovery_proof, execute_multi_agent_loop  # noqa: E402


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



def test_proof_sync_validator_accepts_current_bounded_multi_project_surface() -> None:
    snapshot = multi_agent_contract.multi_agent_contract_snapshot()
    boundary = multi_agent_contract.orchestrator_package_boundary_snapshot()

    result = run_task.validate_proof_sync_contract(
        run_task_exports=[
            'execute_multi_agent_loop',
            'multi_agent_contract_snapshot',
            'orchestrator_package_boundary_snapshot',
            'proof_sync_contract_snapshot',
            'validate_proof_sync_contract',
        ],
        multi_agent_loop_exports=['execute_multi_agent_loop', 'run_multi_agent_controller_cycle', 'run_multi_agent_task_cycle'],
        compatibility_result={
            'processed_task_ids': ['alpha'],
            'verification_authority': 'local_only',
            'controller_final_decision': 'continue',
            'runtime_portability_scope': 'python_only',
        },
        canonical_result={
            'builder_artifact': {},
            'verifier_artifact': {},
            'controller_decision': {},
            'role_handoff_state': {},
        },
        manifest_examples=[{'task_path': 'external-app/tasks/alpha.md'}, {'path': 'external-app/tasks/beta.md', 'depends_on': ['alpha']}],
        role_snapshot=snapshot,
        boundary_snapshot=boundary,
        claim_texts=[
            Path('README.md').read_text(encoding='utf-8'),
            Path('docs/ORCHESTRATOR_PRODUCT_SPEC.md').read_text(encoding='utf-8'),
            Path('docs/TRADINGBOT_PROJECT_STATE.md').read_text(encoding='utf-8'),
        ],
    )

    assert result['ok'] is True
    assert result['issues'] == []



def test_supervised_mixed_manifest_progression_is_bounded_and_truthful() -> None:
    manifest = {
        "tasks": [
            {"task_path": "tasks/089_orchestrator_hardened_autonomous_short_manifest_proof.md", "task_family": "proof_docs"},
            {"task_path": "tasks/106_orchestrator_external_workspace_bootstrap_recovery_proof.md", "task_family": "bootstrap"},
            {"task_path": "tasks/107_orchestrator_supervised_mixed_manifest_autonomy_reproof.md", "task_family": "consumer_facing"},
        ]
    }

    def choose_next_role(ctx: dict[str, object]) -> str:
        phase = str(ctx.get("phase") or "")
        if phase == "build":
            return "builder"
        if phase == "verify":
            return "verifier"
        return "controller"

    def run_role(role: str, ctx: dict[str, object]) -> dict[str, object]:
        if role == "builder":
            return {"status": "built", "task_path": str(ctx["task_path"]) }
        if role == "verifier":
            return {
                "accepted": True,
                "verification_authority": "local_only",
                "task_path": str(ctx["task_path"]),
            }
        return {
            "controller_final_decision": "continue",
            "post_task_decision": "continue",
        }

    result = execute_multi_agent_loop(task_manifest=manifest, choose_next_role=choose_next_role, run_role=run_role)
    normalized = run_task.normalize_multi_agent_loop_result(result)

    assert normalized["count"] == 3
    assert normalized["runtime_portability_scope"] == "python_only"
    assert normalized["verification_authority"] == "local_only"
    assert normalized["controller_final_decision"] == "continue"
    assert normalized["processed_task_ids"] == [
        "089_orchestrator_hardened_autonomous_short_manifest_proof",
        "106_orchestrator_external_workspace_bootstrap_recovery_proof",
        "107_orchestrator_supervised_mixed_manifest_autonomy_reproof",
    ]



def test_supervised_mixed_manifest_stops_conservatively_when_authority_unsatisfied() -> None:
    manifest = {
        "tasks": [
            {"task_path": "tasks/106_orchestrator_external_workspace_bootstrap_recovery_proof.md", "task_family": "bootstrap"},
            {"task_path": "tasks/107_orchestrator_supervised_mixed_manifest_autonomy_reproof.md", "task_family": "consumer_facing"},
        ]
    }

    def choose_next_role(ctx: dict[str, object]) -> str:
        phase = str(ctx.get("phase") or "")
        if phase == "build":
            return "builder"
        if phase == "verify":
            return "verifier"
        return "controller"

    def run_role(role: str, ctx: dict[str, object]) -> dict[str, object]:
        if role == "builder":
            return {"status": "built", "task_path": str(ctx["task_path"])}
        if role == "verifier":
            return {
                "accepted": False,
                "verification_authority": "local_plus_required_ci",
                "verification_authority_satisfied": False,
                "task_path": str(ctx["task_path"]),
            }
        return {
            "controller_final_decision": "stop",
            "post_task_decision": "stop",
            "stopped_reason": "verification authority unsatisfied",
        }

    result = execute_multi_agent_loop(task_manifest=manifest, choose_next_role=choose_next_role, run_role=run_role)
    normalized = run_task.normalize_multi_agent_loop_result(result)

    assert normalized["count"] == 1
    assert normalized["runtime_portability_scope"] == "python_only"
    assert normalized["verification_authority"] == "local_plus_required_ci"
    assert normalized["controller_final_decision"] == "stop"
    assert normalized["processed_task_ids"] == [
        "106_orchestrator_external_workspace_bootstrap_recovery_proof",
    ]



def test_external_workspace_bootstrap_recovery_proof_is_exposed() -> None:
    proof = execute_external_workspace_bootstrap_recovery_proof()

    assert proof["bootstrap_recovery_proof_completed"] is True
    assert proof["controller_final_decision"] == "continue"
    assert proof["runtime_portability_scope"] == "python_only"

    blocked = proof["initial_bootstrap_truth"]
    recovered = proof["recovered_bootstrap_truth"]

    assert blocked["bootstrap_status"] == "blocked"
    assert recovered["previous_bootstrap_status"] == "blocked"
    assert recovered["bootstrap_status"] == "succeeded"
    assert recovered["bootstrap_recovered"] is True


def test_multi_agent_loop_emits_tester_critique_bundle_for_targeted_replay() -> None:
    def _builder(_role_state: dict[str, object]) -> dict[str, object]:
        return {"changed_files": ["agents/lib/multi_agent_loop.py"], "summary": "builder updated loop seam"}

    def _verifier(_builder_artifact: dict[str, object], _role_state: dict[str, object]) -> dict[str, object]:
        return {
            "validator_ok": False,
            "validator_note": "collection import failure",
            "failure_category": "collection_import_failure",
            "failure_message": "ERROR collecting tests/test_multi_project_adapters.py\nImportError while importing test module\ncannot import name 'run_multi_agent_controller_cycle' from 'agents.lib.multi_agent_loop'",
            "focused_results": ["pytest -q tests/test_multi_project_adapters.py"],
            "full_results": ["pytest -q"],
            "acceptance_report": {
                "acceptance_decision": "retryable_failure",
                "post_task_decision": "stop",
                "next_task_may_proceed": False,
                "note": "collection import failure",
            },
        }

    result = execute_multi_agent_loop(
        task_path="external-app/tasks/alpha.md",
        builder_step=_builder,
        verifier_step=_verifier,
    )

    critique = result["verifier_artifact"]["tester_critique_bundle"]
    assert critique["likely_failure_family"] == "import_contract"
    assert critique["focused_replay_commands"] == ["pytest -q tests/test_multi_project_adapters.py"]
    assert critique["broad_replay_commands"] == ["pytest -q"]
    assert "agents/lib/multi_agent_loop.py" in critique["likely_touched_files"]
    assert result["failure_journal_context"]["tester_critique_summary"]["likely_failure_family"] == "import_contract"
