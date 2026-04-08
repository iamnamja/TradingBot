from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load(name: str):
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return importlib.import_module(name)


def test_public_compatibility_contract_snapshot_is_frozen() -> None:
    compat = _load("agents.lib.public_compat")
    snapshot = compat.compatibility_contract_snapshot()

    assert snapshot["public_compatibility_frozen"] is True
    assert "task" in snapshot["manifest_entry_path_aliases"]
    assert "workspace_root" in snapshot["project_convenience_keys"]
    assert set(snapshot["manual_patch_batch_statuses"]) == {"manual_patch", "manual_patch_required"}


def test_failure_record_aliases_are_coerced_through_contract() -> None:
    compat = _load("agents.lib.public_compat")

    canonical = compat.coerce_failure_record_fields({
        "failure_kind": "portfolio_scheduler",
        "failure_message": "blocked",
        "failure_category": "authority_gate",
    })
    legacy = compat.coerce_failure_record_fields({
        "kind": "portfolio_scheduler",
        "message": "blocked",
        "category": "authority_gate",
    })

    assert canonical == legacy
    assert canonical["failure_kind"] == "portfolio_scheduler"


def test_project_contract_convenience_keys_are_applied_consistently() -> None:
    compat = _load("agents.lib.public_compat")
    contract = compat.apply_project_contract_convenience_keys(
        {"project_id": "generic_python_external", "project_workspace_root": "external_repo", "project_branch_namespace": "project/generic_python_external", "project_state_namespace": "project_state/generic_python_external", "project_checkpoint_namespace": "project_checkpoint/generic_python_external"}
    )

    assert contract["workspace_root"] == "external_repo"
    assert contract["branch_namespace"] == "project/generic_python_external"
    assert contract["state_namespace"] == "project_state/generic_python_external"
    assert contract["checkpoint_namespace"] == "project_checkpoint/generic_python_external"
    assert contract["carry_forward_memory_namespace"] == "carry_forward/generic_python_external"


def test_manual_patch_status_is_normalized_to_required_form() -> None:
    compat = _load("agents.lib.public_compat")
    assert compat.canonical_manual_patch_batch_status("manual_patch") == "manual_patch_required"
    assert compat.canonical_manual_patch_batch_status("manual_patch_required") == "manual_patch_required"
