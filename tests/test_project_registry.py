from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _bootstrap_repo_root() -> None:
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _load_project_registry_module():
    _bootstrap_repo_root()
    return importlib.import_module('agents.lib.project_registry')


def _load_task_contracts_module():
    _bootstrap_repo_root()
    return importlib.import_module('agents.lib.task_contracts')


def test_project_registry_snapshot_is_deterministic_and_serializable() -> None:
    registry = _load_project_registry_module()
    snapshot = registry.project_registry_snapshot()

    assert snapshot['deterministic_and_serializable'] is True
    assert set(snapshot['registered_project_ids']) >= {'tradingbot_monorepo', 'generic_python_external'}
    assert snapshot['unattended_safe_project_ids'] == []
    assert 'supervised_local_first' in snapshot['autonomy_lanes']


def test_tradingbot_project_contract_resolves_workspace_validation_and_branch_policy() -> None:
    registry = _load_project_registry_module()
    contract = registry.resolve_project_contract('tradingbot_monorepo')

    assert contract['project_id'] == 'tradingbot_monorepo'
    assert contract['repo_root'] == '.'
    assert contract['workspace_type'] == 'monorepo_python'
    assert contract['allowed_autonomy_lane'] == 'supervised_local_first'
    assert contract['allow_unattended_execution'] is False
    assert contract['validation_contract']['full_validation_commands'] == ['ruff check .', 'pytest -q']
    assert contract['branch_policy']['branch_naming_pattern'] == 'feature/*'


def test_generic_external_python_contract_is_not_unattended_safe() -> None:
    registry = _load_project_registry_module()
    contract = registry.resolve_project_contract('generic_python_external')

    assert contract['workspace_type'] == 'external_python'
    assert contract['allowed_autonomy_lane'] == 'supervised_local_first'
    assert contract['allow_unattended_execution'] is False
    assert contract['workspace_contract']['consumer_name'] == 'generic_python'


def test_task_contracts_surface_project_registry_context() -> None:
    task_contracts = _load_task_contracts_module()
    context = task_contracts.project_registry_task_context(
        [
            'agents/lib/project_registry.py',
            'tests/test_project_registry.py',
        ]
    )

    assert context['touches_project_registry_contract'] is True
    assert 'tradingbot_monorepo' in context['registered_project_ids']
    assert 'external_python' in context['supported_project_workspace_types']
