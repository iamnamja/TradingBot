from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _bootstrap_repo_root() -> None:
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _load(name: str):
    _bootstrap_repo_root()
    return importlib.import_module(name)


def test_controller_contract_exposes_canonical_stop_vocabulary_snapshot() -> None:
    contract = _load("agents.lib.controller_contract")
    snapshot = contract.controller_contract_snapshot()

    assert snapshot["batch_statuses"] == [
        "active",
        "completed",
        "blocked",
        "failed",
        "manual_patch_required",
        "failed_merge",
        "failed_checks",
        "failed_reset",
    ]
    assert snapshot["post_task_decision_aliases"]["checks_failed"] == "failed_checks"
    assert snapshot["batch_status_aliases"]["manual_patch"] == "manual_patch_required"


def test_stop_vocabulary_aliases_normalize_to_canonical_values() -> None:
    contract = _load("agents.lib.controller_contract")

    assert contract.coerce_acceptance_decision("manual") == "manual_patch"
    assert contract.coerce_post_task_decision("checks_failed") == "failed_checks"
    assert contract.coerce_post_task_decision("manual_patch_required") == "manual_patch"
    assert contract.coerce_batch_status("manual_patch") == "manual_patch_required"
    assert contract.coerce_batch_status("stopped") == "blocked"


def test_batch_status_for_post_task_decision_is_conservative_and_explicit() -> None:
    contract = _load("agents.lib.controller_contract")

    assert contract.batch_status_for_post_task_decision(default_status="active", post_task_decision="continue") == "active"
    assert contract.batch_status_for_post_task_decision(default_status="active", post_task_decision="manual_patch") == "manual_patch_required"
    assert contract.batch_status_for_post_task_decision(default_status="active", post_task_decision="blocked") == "blocked"
    assert contract.batch_status_for_post_task_decision(default_status="active", post_task_decision="failed_checks") == "failed_checks"
    assert contract.batch_status_for_post_task_decision(default_status="active", post_task_decision="stop") == "failed"


def test_batch_state_persists_canonical_manual_patch_vocabulary(tmp_path: Path) -> None:
    task_queue = _load("agents.lib.task_queue")
    batch_state = _load("agents.lib.batch_state")

    task_path = tmp_path / "tasks" / "001.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text("# task\n", encoding="utf-8")

    manifest = {"tasks": ["tasks/001.md"]}
    queue = task_queue.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = batch_state.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)
    state = batch_state.advance_task_status(state, task_index=0, to_status="running", status_note="running", event_ts=2)
    state = batch_state.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="manual_patch",
        post_task_decision="manual_patch",
        note="needs manual patch",
        updated_ts=3,
        acceptance_decision="manual_patch",
        retry_count=0,
        next_task_may_proceed=False,
    )

    assert state.batch_status == "manual_patch_required"
    assert state.post_task_decision == "manual_patch"
    assert state.checkpoints[-1].post_task_decision == "manual_patch"
