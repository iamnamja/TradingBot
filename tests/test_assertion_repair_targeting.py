from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_controller_repair_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if "agents.lib.controller_repair" in sys.modules:
        del sys.modules["agents.lib.controller_repair"]
    return importlib.import_module("agents.lib.controller_repair")


def _load_failure_journal_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if "agents.lib.failure_journal" in sys.modules:
        del sys.modules["agents.lib.failure_journal"]
    return importlib.import_module("agents.lib.failure_journal")


def test_assertion_targeting_prefers_missing_alias_repairs() -> None:
    repair = _load_controller_repair_module()
    route = repair.choose_repair_strategy(
        kind="tests",
        message="TypeError: build_failure_remediation_plan() got an unexpected keyword argument 'repair_attempt_budget'",
        category="tests",
    )

    assert route["repair_strategy"] == "behavioral_test_repair"
    assert route["assertion_target_category"] == "missing_alias"
    assert route["chosen_repair_target"] == "compatibility_alias_only"
    assert route["narrow_repair_selected"] is True
    assert route["repair_target_priority"] == "narrow_first"


def test_assertion_targeting_prefers_missing_exported_key_repairs() -> None:
    repair = _load_controller_repair_module()
    route = repair.choose_repair_strategy(
        kind="tests",
        message="AttributeError: module 'agents.run_task' has no attribute 'project_registry_snapshot'",
        category="tests",
    )

    assert route["assertion_target_category"] == "missing_exported_key"
    assert route["chosen_repair_target"] == "compatibility_alias_only"
    assert route["coupled_repair_set_inferred"] is True
    assert route["compatibility_surface_kind"] == "export_plus_provider"
    assert "agents/run_task.py" in route["target_files"]
    assert "agents/lib/project_registry.py" in route["target_files"]


def test_assertion_targeting_prefers_canonical_enum_repairs() -> None:
    repair = _load_controller_repair_module()
    route = repair.choose_repair_strategy(
        kind="tests",
        message="E       AssertionError: assert 'manual_patch' in {'manual_patch_required', 'stopped'}",
        category="tests",
    )

    assert route["assertion_target_category"] == "wrong_canonical_enum_value"
    assert route["chosen_repair_target"] == "controller_contract_surface"
    assert route["narrow_repair_selected"] is True


def test_assertion_targeting_prefers_project_contract_field_repairs() -> None:
    repair = _load_controller_repair_module()
    route = repair.choose_repair_strategy(
        kind="tests",
        message="KeyError: 'workspace_root'",
        category="tests",
    )

    assert route["assertion_target_category"] == "missing_project_contract_field"
    assert route["chosen_repair_target"] == "compatibility_alias_only"


def test_assertion_targeting_prefers_docs_claim_sync_for_overclaim() -> None:
    repair = _load_controller_repair_module()
    route = repair.choose_repair_strategy(
        kind="tests",
        message="README says Tasks 090–123 are complete but the run failed to reach green within max iterations.",
        category="docs_proof_claim_drift",
    )

    assert route["repair_strategy"] == "docs_proof_claim_repair"
    assert route["assertion_target_category"] == "docs_overclaim"
    assert route["chosen_repair_target"] == "docs_claim_sync"


def test_assertion_targeting_infers_snapshot_field_plus_provider_set() -> None:
    repair = _load_controller_repair_module()
    route = repair.choose_repair_strategy(
        kind="tests",
        message="KeyError: 'portfolio_reproof_retry_task'",
        category="tests",
    )

    assert route["assertion_target_category"] == "missing_project_contract_field"
    assert route["coupled_repair_set_inferred"] is True
    assert route["compatibility_surface_kind"] == "snapshot_plus_provider"
    assert "agents/lib/project_registry.py" in route["target_files"]
    assert "agents/run_task.py" in route["target_files"]


def test_assertion_targeting_infers_enum_contract_plus_consumer_set() -> None:
    repair = _load_controller_repair_module()
    route = repair.choose_repair_strategy(
        kind="tests",
        message="E       AssertionError: assert 'manual_patch' in {'manual_patch_required', 'stopped'}",
        category="tests",
    )

    assert route["assertion_target_category"] == "wrong_canonical_enum_value"
    assert route["chosen_repair_target"] == "controller_contract_surface"
    assert route["coupled_repair_set_inferred"] is True
    assert route["compatibility_surface_kind"] == "enum_contract_plus_consumer"
    assert "agents/lib/controller_contract.py" in route["target_files"]
    assert "agents/lib/batch_executor.py" in route["target_files"]


def test_controller_repair_context_surfaces_coupled_compatibility_set() -> None:
    repair = _load_controller_repair_module()
    context = repair.build_controller_repair_context(
        kind="tests",
        message="AttributeError: module 'agents.run_task' has no attribute 'project_registry_snapshot'",
        category="tests",
    )

    prompt = context["repair_prompt"]
    assert "Coupled compatibility surface:" in prompt
    assert "export_plus_provider" in prompt
    assert "agents/run_task.py" in prompt
    assert "agents/lib/project_registry.py" in prompt


def test_failure_journal_surfaces_chosen_repair_target_in_plan() -> None:
    fj = _load_failure_journal_module()
    plan = fj.build_failure_remediation_plan(
        kind="tests",
        message="AttributeError: module 'agents.run_task' has no attribute 'project_registry_snapshot'",
        category="tests",
        retry_count=1,
        fingerprint="fp-assertion",
        raw_failure_snippet="AttributeError: module 'agents.run_task' has no attribute 'project_registry_snapshot'",
    )

    assert plan["chosen_repair_target"] == "compatibility_alias_only"
    assert plan["assertion_target_category"] == "missing_exported_key"
    assert plan["repair_target_surface"] == "compatibility_alias_only"
    assert plan["coupled_repair_set_inferred"] is True
    assert plan["compatibility_surface_kind"] == "export_plus_provider"
    assert "agents/run_task.py" in plan["compatibility_surface_files"]
    assert "agents/lib/project_registry.py" in plan["compatibility_surface_files"]
