from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _load_public_compat_module():
    _ensure_repo_on_path()
    return importlib.import_module("agents.lib.public_compat")


def _load_project_registry_module():
    _ensure_repo_on_path()
    return importlib.import_module("agents.lib.project_registry")


def _load_failure_journal_module():
    _ensure_repo_on_path()
    return importlib.import_module("agents.lib.failure_journal")


def test_schema_alias_snapshot_reports_normalization_layer() -> None:
    compat = _load_public_compat_module()
    snapshot = compat.compatibility_contract_snapshot()

    assert snapshot["contract_version"] >= 2
    assert snapshot["schema_alias_normalization_enabled"] is True
    assert set(snapshot["failure_remediation_field_aliases"]) >= {"retry_count", "max_repair_attempts"}


def test_manifest_aliases_normalize_to_equivalent_payloads() -> None:
    compat = _load_public_compat_module()

    via_path = compat.normalize_manifest_entry_payload({"path": "tasks/001.md", "depends_on": []}, index=0)
    via_task_path = compat.normalize_manifest_entry_payload({"task_path": "tasks/001.md", "depends_on": []}, index=0)
    via_task = compat.normalize_manifest_entry_payload({"task": "tasks/001.md", "depends_on": []}, index=0)

    assert via_path == via_task_path == via_task
    assert via_path["task_path"] == "tasks/001.md"


def test_failure_aliases_and_budget_aliases_normalize_equivalently() -> None:
    compat = _load_public_compat_module()

    record = compat.normalize_failure_record_payload(kind="validation", message="boom", category="lint")
    remediation = compat.normalize_failure_remediation_payload(kind="validation", message="boom", category="lint", retry_count=1, repair_attempt_budget=2)

    assert record == {
        "failure_kind": "validation",
        "failure_message": "boom",
        "failure_category": "lint",
    }
    assert remediation["max_repair_attempts"] == 2
    assert remediation["repair_attempt_budget"] == 2


def test_project_contract_aliases_normalize_to_convenience_keys() -> None:
    compat = _load_public_compat_module()
    normalized = compat.normalize_project_contract_payload(
        {
            "project_id": "demo",
            "project_workspace_root": "workspace/demo",
            "project_branch_namespace": "project/demo",
            "project_state_namespace": "state/demo",
            "project_checkpoint_namespace": "checkpoint/demo",
        }
    )

    assert normalized["workspace_root"] == "workspace/demo"
    assert normalized["branch_namespace"] == "project/demo"
    assert normalized["state_namespace"] == "state/demo"
    assert normalized["checkpoint_namespace"] == "checkpoint/demo"
    assert normalized["carry_forward_memory_namespace"] == "carry_forward/demo"


def test_failure_journal_consumes_shared_normalizer_for_budget_aliases() -> None:
    fj = _load_failure_journal_module()
    plan = fj.build_failure_remediation_plan(kind="validation", message="project A failed checks", retry_count=1, repair_attempt_budget=2)

    assert plan["max_repair_attempts"] == 2
    assert plan["repair_attempt_budget"] == 2


def test_project_registry_snapshot_reports_alias_normalization_enabled() -> None:
    registry = _load_project_registry_module()
    snapshot = registry.project_registry_snapshot()

    assert snapshot["schema_alias_normalization_enabled"] is True
