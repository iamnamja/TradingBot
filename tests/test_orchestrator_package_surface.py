
from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_modules():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    run_task = importlib.import_module('agents.run_task')
    multi_agent_contract = importlib.import_module('agents.lib.multi_agent_contract')
    project_workspace_adapter = importlib.import_module('agents.lib.project_workspace_adapter')
    return run_task, multi_agent_contract, project_workspace_adapter


def test_public_orchestrator_boundary_is_explicit_but_not_fully_extracted() -> None:
    run_task, multi_agent_contract, _ = _load_modules()

    assert callable(run_task.orchestrator_package_boundary_snapshot)
    assert callable(run_task.consumer_bridge_requirements)
    snapshot = multi_agent_contract.orchestrator_package_boundary_snapshot()

    assert snapshot['product_name'] == 'orchestrator'
    assert snapshot['operates_inside_monorepo'] is True
    assert snapshot['full_standalone_extraction_completed'] is False
    assert 'tradingbot' in snapshot['supported_consumers']
    assert 'generic_python' in snapshot['supported_consumers']


def test_consumer_bridge_contract_isolated_from_reusable_orchestrator_surface() -> None:
    _, _, project_workspace_adapter = _load_modules()

    tradingbot = project_workspace_adapter.consumer_bridge_contract(project_workspace_adapter.tradingbot_workspace_contract('.'))
    generic = project_workspace_adapter.consumer_bridge_contract(project_workspace_adapter.generic_python_workspace_contract('external-app'))

    assert tradingbot['consumer_name'] == 'tradingbot'
    assert generic['consumer_name'] == 'generic_python'
    assert generic['workspace_root'] == 'external-app'
    assert tradingbot['protected_paths'] != generic['protected_paths']
    assert 'required_bridge_fields' in tradingbot
    assert 'optional_bridge_fields' in tradingbot
    assert tradingbot['full_standalone_extraction_completed'] is False


def test_run_task_wrappers_preserve_consumer_bridge_surface() -> None:
    run_task, _, _ = _load_modules()

    bridge = run_task.consumer_bridge_snapshot()
    boundary = run_task.orchestrator_package_boundary_snapshot()

    assert 'tradingbot' in bridge['supported_consumers']
    assert 'generic_python' in bridge['supported_consumers']
    assert boundary['consumer_bridge']['consumer_bridge_is_stable'] is True
