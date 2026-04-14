from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

from .resume_state import AttemptStateRecord, CheckpointStage, ResumeCheckpoint

DEFAULT_STATE_FILENAME = "attempt_state.json"

__all__ = [
    "init_attempt_state",
    "load_attempt_state",
    "record_checkpoint",
    "mark_failure",
    "mark_manual_intervention",
    "attempt_kind",
    "plan_reentry",
    "determine_reentry",
]


def _state_path(root: Path | str) -> Path:
    root_path = Path(root)
    return root_path / DEFAULT_STATE_FILENAME


def _atomic_write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    tmp_path.replace(path)


def init_attempt_state(root: Path | str, attempt_id: str) -> AttemptStateRecord:
    """
    Initialize a new attempt state if not present; otherwise load the existing one.
    """
    path = _state_path(root)
    if path.exists():
        return load_attempt_state(root)

    now = time.time()
    state = AttemptStateRecord(
        attempt_id=attempt_id,
        created_at=now,
        updated_at=now,
        last_checkpoint=None,
        failure_count=0,
        manual_intervention=False,
        checkpoint_history=[],
    )
    _atomic_write_json(path, state.to_dict())
    return state


def load_attempt_state(root: Path | str) -> AttemptStateRecord:
    """
    Load attempt state. If the state file is missing or corrupted, return a state that
    forces a conservative restart (manual_intervention=True).
    """
    path = _state_path(root)
    if not path.exists():
        now = time.time()
        # Unknown attempt id; force conservative posture.
        return AttemptStateRecord(
            attempt_id="unknown",
            created_at=now,
            updated_at=now,
            last_checkpoint=None,
            failure_count=0,
            manual_intervention=True,
            checkpoint_history=[],
        )
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return AttemptStateRecord.from_dict(data)
    except Exception:
        # Corrupted or ambiguous state: force safe restart
        now = time.time()
        return AttemptStateRecord(
            attempt_id="unknown",
            created_at=now,
            updated_at=now,
            last_checkpoint=None,
            failure_count=0,
            manual_intervention=True,
            checkpoint_history=[],
        )


def _save_state(root: Path | str, state: AttemptStateRecord) -> AttemptStateRecord:
    state.updated_at = time.time()
    _atomic_write_json(_state_path(root), state.to_dict())
    return state


def record_checkpoint(
    root: Path | str,
    stage: CheckpointStage,
    surface: str,
    *,
    safe: bool = True,
    details: Optional[Dict] = None,
) -> AttemptStateRecord:
    """
    Record a resume-safe checkpoint representing the last safe transition point
    and the intended re-entry surface.
    """
    state = load_attempt_state(root)
    cp = ResumeCheckpoint(stage=stage, surface=surface, ts=time.time(), safe=safe, details=details or {})
    state.last_checkpoint = cp
    state.checkpoint_history.append(cp)
    return _save_state(root, state)


def mark_failure(root: Path | str) -> AttemptStateRecord:
    """
    Mark a failure against the attempt. This does not change the resume checkpoint,
    but it changes the attempt kind when deciding re-entry.
    """
    state = load_attempt_state(root)
    state.failure_count += 1
    return _save_state(root, state)


def mark_manual_intervention(root: Path | str, note: Optional[str] = None) -> AttemptStateRecord:
    """
    Mark that manual intervention occurred before resume. This will conservatively
    force a restart unless the operator explicitly overrides behavior.
    """
    state = load_attempt_state(root)
    state.manual_intervention = True
    # Optionally record an unsafe marker checkpoint for traceability
    details = {"note": note} if note else {}
    cp = ResumeCheckpoint(stage=CheckpointStage.STARTED, surface="restart", ts=time.time(), safe=False, details=details)
    state.last_checkpoint = cp
    state.checkpoint_history.append(cp)
    return _save_state(root, state)


def attempt_kind(state: AttemptStateRecord) -> str:
    """
    Compute a coarse attempt kind for operator visibility and routing:
    - fresh execution
    - retry after failure
    - resume after partial progress
    - manual intervention before resume
    """
    if state.manual_intervention:
        return "manual_intervention"
    if state.failure_count > 0 and not state.last_checkpoint:
        return "retry_after_failure"
    if state.last_checkpoint and state.last_checkpoint.stage not in (CheckpointStage.STARTED,):
        return "resume_after_partial"
    return "fresh_execution"


def plan_reentry(state: AttemptStateRecord) -> Dict[str, str]:
    """
    Decide the conservative re-entry plan:
    - When manual intervention is detected, or checkpoints are unsafe/ambiguous -> restart.
    - Else when a safe checkpoint exists -> resume at its intended surface.
    - Else -> fresh.
    """
    if state.manual_intervention:
        return {
            "mode": "restart",
            "reason": "manual_intervention",
        }

    cp = state.last_checkpoint
    if not cp:
        # No checkpoint recorded; choose safe fresh start
        return {"mode": "fresh"}

    if not cp.safe:
        return {
            "mode": "restart",
            "reason": "unsafe_checkpoint",
        }

    # Known safe stages to resume from; anything else falls back to fresh as a guard.
    safe_resume_stages = {
        CheckpointStage.PRECHECKS_PASSED,
        CheckpointStage.EXECUTION_STARTED,
        CheckpointStage.PARTIAL_PROGRESS,
        CheckpointStage.WORKSPACE_PREPARED,
        CheckpointStage.ADMISSION_OK,
    }
    if cp.stage in safe_resume_stages:
        return {
            "mode": "resume",
            "surface": cp.surface,
            "from_stage": cp.stage.value,
        }

    # For complete/terminal checkpoints, allow a conservative post-completion surface if provided,
    # otherwise restart (safe, deterministic).
    terminal_resume_allowed = {
        CheckpointStage.EXECUTION_COMPLETE,
        CheckpointStage.REVIEW_APPROVED,
        CheckpointStage.MERGE_SAFE,
    }
    if cp.stage in terminal_resume_allowed and cp.surface:
        return {
            "mode": "resume",
            "surface": cp.surface,
            "from_stage": cp.stage.value,
        }

    return {"mode": "fresh"}


def determine_reentry(root: Path | str) -> Dict[str, str]:
    """
    Convenience wrapper that loads state and computes a re-entry plan.
    """
    state = load_attempt_state(root)
    return plan_reentry(state)
