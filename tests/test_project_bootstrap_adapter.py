from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agents.lib import project_workspace_adapter  # noqa: E402

def _builder_bootstrap_exports():
    project_adapter = pytest.importorskip('builder.orchestrator.project_adapter')
    project_config = pytest.importorskip('builder.orchestrator.project_config')
    return (
        project_adapter.bootstrap_project_adapter_scaffold,
        project_adapter.build_bootstrap_starter_docs_text,
        project_adapter.build_bootstrap_task_template_text,
        project_config.bootstrap_project_config_scaffold,
    )


def test_bootstrap_creates_expected_scaffold_deterministically(tmp_path: Path) -> None:
    (
        bootstrap_project_adapter_scaffold,
        _build_bootstrap_starter_docs_text,
        _build_bootstrap_task_template_text,
        bootstrap_project_config_scaffold,
    ) = _builder_bootstrap_exports()
    cfg_path = bootstrap_project_config_scaffold(tmp_path)
    generated = bootstrap_project_adapter_scaffold(tmp_path)

    assert cfg_path == tmp_path / 'orchestrator_project_config.json'
    assert generated['docs'] == tmp_path / 'docs' / 'orchestrator_starter.md'
    assert generated['task_template'] == tmp_path / 'tasks' / 'task_template.md'
    assert generated['task_example'] == tmp_path / 'tasks' / '001_example_task.md'
    assert generated['adapter_factory'] == tmp_path / 'src' / 'builder' / 'orchestrator' / 'project_adapter_factory.py'
    assert generated['validator_config'] == tmp_path / '.orchestrator_validator.json'

    cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    assert cfg['tasks_directory'] == 'tasks/'
    assert cfg['lint_command'] == 'ruff check .'
    assert cfg['test_command'] == 'pytest -q'


def test_generated_scaffold_is_generic_reusable_starting_point(tmp_path: Path) -> None:
    (
        bootstrap_project_adapter_scaffold,
        _build_bootstrap_starter_docs_text,
        _build_bootstrap_task_template_text,
        bootstrap_project_config_scaffold,
    ) = _builder_bootstrap_exports()
    bootstrap_project_config_scaffold(tmp_path)
    bootstrap_project_adapter_scaffold(tmp_path)

    docs_text = (tmp_path / 'docs' / 'orchestrator_starter.md').read_text(encoding='utf-8')
    cfg_text = (tmp_path / 'orchestrator_project_config.json').read_text(encoding='utf-8')
    tmpl_text = (tmp_path / 'tasks' / 'task_template.md').read_text(encoding='utf-8')

    assert 'TradingBot' not in docs_text
    assert 'TradingBot' not in cfg_text
    assert 'TradingBot' not in tmpl_text
    assert 'generic and reusable' in docs_text


def test_starter_docs_and_template_references_present() -> None:
    (
        _bootstrap_project_adapter_scaffold,
        build_bootstrap_starter_docs_text,
        build_bootstrap_task_template_text,
        _bootstrap_project_config_scaffold,
    ) = _builder_bootstrap_exports()
    docs = build_bootstrap_starter_docs_text()
    template = build_bootstrap_task_template_text()

    assert 'tasks/001_example_task.md' in docs
    assert 'task_template.md' in docs
    assert '## Deliverables' in template
    assert 'ruff check .' in template


def test_bootstrap_logic_lives_outside_run_task_shell() -> None:
    run_task_text = Path('agents/run_task.py').read_text(encoding='utf-8')
    assert 'build_bootstrap_starter_docs_text' not in run_task_text
    assert 'build_bootstrap_task_template_text' not in run_task_text
    assert 'bootstrap_project_adapter_scaffold' in run_task_text
    assert 'bootstrap_project_config_scaffold' in run_task_text


def test_run_task_shell_bootstrap_surface_is_additive() -> None:
    run_task_text = Path('agents/run_task.py').read_text(encoding='utf-8')
    assert 'ap.add_argument("task", nargs="?"' in run_task_text
    assert '--bootstrap-project' in run_task_text
    assert 'Task file path is required unless --bootstrap-project is used.' in run_task_text


def test_workspace_contract_exposes_bootstrap_and_validation_truth() -> None:
    contract = project_workspace_adapter.generic_python_workspace_contract('external-app')

    assert contract['workspace_root'] == 'external-app'
    assert contract['consumer_name'] == 'generic_python'
    assert contract['bootstrap_commands']
    assert contract['validation_commands'] == ['ruff check .', 'pytest -q']
    assert contract['acceptance_evidence_commands'] == ['pytest -q']
    assert contract['merge_policy_constraints']['verification_authority_profile'] == 'local_plus_required_ci'


def test_bootstrap_failures_are_explicit_state_not_hidden_exceptions() -> None:
    contract = project_workspace_adapter.generic_python_workspace_contract('external-app')
    truth = project_workspace_adapter.evaluate_workspace_bootstrap_result(
        contract,
        bootstrap_ok=False,
        bootstrap_error='missing virtualenv',
    )

    assert truth['bootstrap_attempted'] is True
    assert truth['bootstrap_blocked'] is True
    assert truth['bootstrap_status'] == 'blocked'
    assert truth['bootstrap_error'] == 'missing virtualenv'
    assert truth['workspace_ready_for_validation'] is False
    assert project_workspace_adapter.workspace_can_resume_after_bootstrap_failure(truth) is True


def test_bootstrap_success_is_explicit_and_ready_for_validation() -> None:
    contract = project_workspace_adapter.generic_python_workspace_contract('external-app')
    truth = project_workspace_adapter.evaluate_workspace_bootstrap_result(
        contract,
        bootstrap_ok=True,
        bootstrap_error='',
    )

    assert truth['bootstrap_attempted'] is True
    assert truth['bootstrap_blocked'] is False
    assert truth['bootstrap_status'] == 'succeeded'
    assert truth['bootstrap_error'] == ''
    assert truth['workspace_ready_for_validation'] is True


def test_bootstrap_recovery_from_blocked_state_is_truthful_and_resumable() -> None:
    contract = project_workspace_adapter.generic_python_workspace_contract('external-app')
    blocked = project_workspace_adapter.evaluate_workspace_bootstrap_result(
        contract,
        bootstrap_ok=False,
        bootstrap_error='missing virtualenv',
    )
    recovered = project_workspace_adapter.recover_workspace_bootstrap_truth(
        blocked,
        bootstrap_ok=True,
        bootstrap_error='',
    )

    assert blocked['bootstrap_status'] == 'blocked'
    assert recovered['previous_bootstrap_status'] == 'blocked'
    assert recovered['recovery_attempted'] is True
    assert recovered['resumed_from_bootstrap_blocked_state'] is True
    assert recovered['bootstrap_status'] == 'succeeded'
    assert recovered['bootstrap_recovered'] is True
    assert recovered['workspace_ready_for_validation'] is True


def test_bootstrap_recovery_snapshot_stays_python_first_and_narrow() -> None:
    snapshot = project_workspace_adapter.bootstrap_recovery_proof_snapshot()

    assert snapshot['python_first_scope_only'] is True
    assert snapshot['recovery_proof_scope'] == 'simple_external_python_workspace'
    assert snapshot['supports_truthful_blocked_then_recovered_state'] is True
    assert snapshot['bootstrap_statuses'] == ['not_started', 'succeeded', 'blocked']


def test_tradingbot_workspace_contract_includes_runtime_artifact_policy_paths() -> None:
    contract = project_workspace_adapter.tradingbot_workspace_contract('.')

    assert '_last_agent_model_output.txt' in contract['artifact_output_paths']
    assert '_last_agent_file_bundle.txt' in contract['artifact_output_paths']
    assert '_last_agent_file_bundle_error.txt' in contract['artifact_output_paths']
    assert '_last_subset_preservation.json' in contract['artifact_output_paths']
