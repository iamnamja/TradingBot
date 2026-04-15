from __future__ import annotations

from pathlib import Path

from agents.lib.attempt_state import (
    attempt_kind,
    determine_reentry,
    init_attempt_state,
    load_attempt_state,
    mark_manual_intervention,
    record_checkpoint,
)
from agents.lib.resume_state import CheckpointStage
from agents.lib.bounded_pilot import run_bounded_two_task_pilot


def test_resume_successful_reentry(tmp_path: Path) -> None:
    # Fresh attempt initialization
    state = init_attempt_state(tmp_path, attempt_id="a1")
    assert attempt_kind(state) in {"fresh_execution", "resume_after_partial"}  # initial could be fresh

    # Record a safe checkpoint after prechecks with a clear re-entry surface
    record_checkpoint(tmp_path, CheckpointStage.PRECHECKS_PASSED, surface="run_execution", safe=True)

    # Simulate process crash or interruption: re-load from disk
    loaded = load_attempt_state(tmp_path)
    plan = determine_reentry(tmp_path)

    assert loaded.last_checkpoint is not None
    assert plan["mode"] == "resume"
    assert plan["surface"] == "run_execution"
    assert plan["from_stage"] == CheckpointStage.PRECHECKS_PASSED.value
    # The plan should explicitly mark precision as precise
    assert plan["precision"] == "precise"

    # The attempt kind should now indicate resume-after-partial
    assert attempt_kind(loaded) == "resume_after_partial"


def test_conservative_fallback_on_manual_intervention(tmp_path: Path) -> None:
    # Initialize and then mark manual intervention to force conservative restart
    init_attempt_state(tmp_path, attempt_id="a2")
    mark_manual_intervention(tmp_path, note="operator adjusted branch hygiene")

    plan = determine_reentry(tmp_path)
    assert plan["mode"] == "restart"
    assert plan.get("reason") == "manual_intervention"
    # Manual intervention must force a broad rerun posture
    assert plan.get("precision") == "broad"


def test_bounded_pilot_ledger_persists_adjacent_pair_resume_truth(tmp_path: Path) -> None:
    # Prepare two adjacent tasks; Task B follows A and declares a precise resume plan
    tasks = [
        {
            "id": "task-A",
            "admit": True,
            "run": lambda task, role: {"ok": True},
            # optional plan on A (will be overridden by B if both present)
            "resume_plan": {"mode": "resume", "surface": "dev_to_test", "precision": "broad"},
        },
        {
            "id": "task-B",
            "admit": True,
            "follows": "task-A",
            "run": lambda task, role: {"ok": True},
            "resume_plan": {"mode": "resume", "surface": "dev_to_test", "precision": "precise"},
        },
    ]

    _, ledger = run_bounded_two_task_pilot(tasks, artifact_dir=str(tmp_path))

    assert "resume_truth" in ledger
    assert ledger["resume_truth"]["mode"] == "resume"
    assert ledger["resume_truth"]["precision"] == "precise"
    assert ledger["resume_truth"]["source"] == "task_payload"
