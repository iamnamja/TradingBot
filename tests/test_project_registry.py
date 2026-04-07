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
    return importlib.import_module("agents.lib.project_registry")


def test_project_registry_snapshot_exposes_validation_matrix_by_project() -> None:
    registry = _load_project_registry_module()
    snapshot = registry.project_registry_snapshot()

    assert snapshot["deterministic_and_serializable"] is True
    assert set(snapshot["registered_project_ids"]) >= {"tradingbot_monorepo", "generic_python_external"}
    assert set(snapshot["supported_authority_profiles"]) >= {"local_only", "local_plus_required_ci"}
    assert set(snapshot["validation_matrix_by_project"]) >= {"tradingbot_monorepo", "generic_python_external"}


def test_project_validation_matrix_differs_across_projects() -> None:
    registry = _load_project_registry_module()

    tradingbot = registry.project_validation_matrix(registry.resolve_project_contract("tradingbot_monorepo"))
    generic = registry.project_validation_matrix(registry.resolve_project_contract("generic_python_external"))

    assert tradingbot["bootstrap_required"] is False
    assert generic["bootstrap_required"] is True
    assert tradingbot["verification_authority_profile"] == "local_plus_required_ci"
    assert generic["verification_authority_profile"] == "local_only"
    assert tradingbot["repo_required_checks"] == ["ci"]
    assert generic["repo_required_checks"] == []


def test_project_validation_plan_resolves_by_scope_and_project_id() -> None:
    registry = _load_project_registry_module()

    focused = registry.resolve_project_validation_plan("tradingbot_monorepo", validation_scope="focused")
    full = registry.resolve_project_validation_plan("generic_python_external", validation_scope="full")

    assert focused["project_id"] == "tradingbot_monorepo"
    assert focused["validation_scope"] == "focused"
    assert focused["commands"] == ["pytest -q tests/test_run_task_runtime_foundations.py"]

    assert full["project_id"] == "generic_python_external"
    assert full["validation_scope"] == "full"
    assert full["commands"] == ["ruff check .", "pytest -q"]
