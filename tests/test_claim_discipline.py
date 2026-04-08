from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_claim_discipline_module():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return importlib.import_module("agents.lib.claim_discipline")


def _load_run_task():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return importlib.import_module("agents.run_task")


def test_proof_complete_wording_is_blocked_when_validation_is_red() -> None:
    cd = _load_claim_discipline_module()
    updates = {
        "docs/TRADINGBOT_PROJECT_STATE.md": "Tasks 090–128 are complete.",
        "docs/ORCHESTRATOR_PRODUCT_SPEC.md": "The synchronized proof checkpoint is now complete through Task 128.",
    }

    decision = cd.evaluate_claim_discipline(
        focused_validation_green=False,
        full_validation_green=False,
        proposed_updates=updates,
    )

    assert decision["proof_claim_updates_allowed"] is False
    assert decision["docs_overclaim_blocked"] is True
    assert set(decision["blocked_claim_paths"]) == set(updates)


def test_truthful_recovery_wording_is_allowed_when_validation_is_red() -> None:
    cd = _load_claim_discipline_module()
    updates = {
        "docs/TRADINGBOT_PROJECT_STATE.md": "Recovery is still in progress and proof claims remain bounded to green validation.",
    }

    decision = cd.evaluate_claim_discipline(
        focused_validation_green=False,
        full_validation_green=False,
        proposed_updates=updates,
    )

    assert decision["proof_claim_updates_allowed"] is False
    assert decision["docs_overclaim_blocked"] is False
    assert decision["blocked_claim_paths"] == []


def test_proof_complete_wording_is_allowed_only_after_focused_and_full_green() -> None:
    cd = _load_claim_discipline_module()
    updates = {
        "docs/ORCHESTRATOR_PRODUCT_SPEC.md": "The synchronized proof checkpoint is now complete through Task 128.",
    }

    partial = cd.evaluate_claim_discipline(
        focused_validation_green=True,
        full_validation_green=False,
        proposed_updates=updates,
    )
    full = cd.evaluate_claim_discipline(
        focused_validation_green=True,
        full_validation_green=True,
        proposed_updates=updates,
    )

    assert partial["proof_claim_updates_allowed"] is False
    assert partial["blocked_claim_paths"] == ["docs/ORCHESTRATOR_PRODUCT_SPEC.md"]
    assert full["proof_claim_updates_allowed"] is True
    assert full["blocked_claim_paths"] == []


def test_filter_claim_updates_drops_overclaims_until_green() -> None:
    cd = _load_claim_discipline_module()
    updates = {
        "docs/TRADINGBOT_PROJECT_STATE.md": "Tasks 090–128 are complete.",
        "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md": "Recovery remains in progress.",
    }

    filtered = cd.filter_claim_updates_for_validation(
        focused_validation_green=False,
        full_validation_green=False,
        proposed_updates=updates,
    )

    assert "docs/TRADINGBOT_PROJECT_STATE.md" not in filtered["allowed_updates"]
    assert "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md" in filtered["allowed_updates"]


def test_run_task_claim_discipline_helpers_are_available() -> None:
    run_task = _load_run_task()
    updates = {"docs/TRADINGBOT_PROJECT_STATE.md": "Tasks 090–128 are complete."}

    assert callable(run_task.claim_discipline_snapshot)
    assert callable(run_task.contains_proof_complete_claim)
    assert callable(run_task.evaluate_claim_discipline)
    assert callable(run_task.filter_claim_updates_for_validation)

    decision = run_task.evaluate_claim_discipline(
        focused_validation_green=False,
        full_validation_green=False,
        proposed_updates=updates,
    )
    assert decision["docs_overclaim_blocked"] is True
