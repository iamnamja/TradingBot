from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Tuple, Optional

__all__ = [
    "run_bounded_two_task_pilot",
    "_read_ledger",
]


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _admission_truth(task_a: Dict[str, Any], task_b: Dict[str, Any]) -> Dict[str, Any]:
    # Conservative admission: both tasks must explicitly admit True
    admit_a = bool(task_a.get("admit", False))
    admit_b = bool(task_b.get("admit", False))
    accepted = admit_a and admit_b
    reason = None
    if not accepted:
        reason = "admission denied for one or both tasks"
    return {"accepted": accepted, "reason": reason}


def _handoff_eligible(task_a: Dict[str, Any], task_b: Dict[str, Any]) -> Dict[str, Any]:
    # Task B must explicitly follow Task A by id
    a_id = task_a.get("id")
    follows = task_b.get("follows")
    eligible = a_id is not None and follows == a_id
    reason = None if eligible else "task B is not an explicit adjacent follow-on to task A"
    return {"eligible": eligible, "reason": reason}


def _pair_ledger_path(artifact_dir: str, pair_id: str) -> str:
    # Directory convention: <artifact_dir>/two_task_pilot/pairs/<pair_id>.json
    base = os.path.join(artifact_dir, "two_task_pilot", "pairs")
    _ensure_dir(base)
    return os.path.join(base, f"{pair_id}.json")


def _write_ledger(ledger_path: str, ledger: Dict[str, Any]) -> None:
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, sort_keys=False)


def _read_ledger(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _coerce_resume_truth(task_a: Dict[str, Any], task_b: Dict[str, Any], *, handoff_ok: bool) -> Dict[str, str]:
    """
    Persist a tiny adjacent-pair resume-truth summary:
    - Prefer an explicit 'resume_plan' dict on either task (B overrides A).
    - Else infer 'unknown' with conservative defaults.
    """
    plan_obj = {}
    if isinstance(task_a.get("resume_plan"), dict):
        plan_obj = dict(task_a.get("resume_plan") or {})
    if isinstance(task_b.get("resume_plan"), dict):
        # B takes precedence if provided
        plan_obj = dict(task_b.get("resume_plan") or {}) or plan_obj

    mode = str(plan_obj.get("mode", "")).strip()
    surface = str(plan_obj.get("surface", "")).strip()
    precision = str(plan_obj.get("precision", "")).strip().lower()

    if not precision:
        if mode == "resume" and surface:
            precision = "precise"
        elif mode in {"fresh", "restart"}:
            precision = "broad"
        else:
            precision = "unknown"

    if not mode:
        mode = "unknown"

    source = "task_payload" if plan_obj else "inferred"
    if source == "inferred" and handoff_ok:
        # With an eligible adjacent handoff but no explicit plan, keep precision unknown rather than
        # guessing at broad or precise.
        mode = "default" if mode == "unknown" else mode
        precision = "unknown"

    return {"mode": mode, "precision": precision, "source": source}


def run_bounded_two_task_pilot(
    tasks: List[Dict[str, Any]],
    artifact_dir: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    # Prepare artifacts directory
    if artifact_dir is None:
        artifact_dir = os.path.join(os.getcwd(), "artifacts")

    # Initialize pair/session id and ledger skeleton
    pair_id = str(uuid.uuid4())
    role_sequence = ["dev", "test"]
    supervision_required = True

    # Basic manifest validation
    manifest_ok = len(tasks) == 2

    task_a: Dict[str, Any] = tasks[0] if len(tasks) >= 1 else {}
    task_b: Dict[str, Any] = tasks[1] if len(tasks) >= 2 else {}

    task_a_id = task_a.get("id")
    task_b_id = task_b.get("id")

    # Admission and handoff evaluation (only meaningful if we have two tasks)
    if manifest_ok:
        admission = _admission_truth(task_a, task_b)
        handoff = _handoff_eligible(task_a, task_b)
    else:
        admission = {"accepted": False, "reason": "requires exactly two tasks"}
        handoff = {"eligible": False, "reason": "requires exactly two tasks"}

    resume_truth = _coerce_resume_truth(task_a, task_b, handoff_ok=bool(handoff.get("eligible", False)))

    ledger: Dict[str, Any] = {
        "pair_id": pair_id,
        "task_a_id": task_a_id,
        "task_b_id": task_b_id,
        "admission": admission,
        "handoff": handoff,
        "role_sequence": role_sequence,
        "supervision_required": supervision_required,
        "resume_truth": resume_truth,
        "outcome": "rejected",  # default; may become success/failed
        "tasks": [],
    }

    # Determine whether to run
    if not manifest_ok or not admission["accepted"] or not handoff["eligible"]:
        # Persist and return the rejection ledger
        ledger_path = _pair_ledger_path(artifact_dir, pair_id)
        _write_ledger(ledger_path, ledger)
        return ledger_path, ledger

    # Execute bounded supervised two-task pilot: dev(A) -> test(B)
    try:
        # Execute Task A with "dev" role
        role_a = "dev"
        run_a = task_a.get("run")
        if callable(run_a):
            result_a = run_a(task_a, role_a)
        else:
            result_a = None
        ledger["tasks"].append(
            {"task_id": task_a_id, "role": role_a, "result": result_a}
        )

        # Execute Task B with "test" role
        role_b = "test"
        run_b = task_b.get("run")
        if callable(run_b):
            result_b = run_b(task_b, role_b)
        else:
            result_b = None
        ledger["tasks"].append(
            {"task_id": task_b_id, "role": role_b, "result": result_b}
        )

        ledger["outcome"] = "success"
    except Exception as exc:  # pragma: no cover - defensive
        ledger["outcome"] = "failed"
        ledger["error"] = str(exc)

    # Persist ledger
    ledger_path = _pair_ledger_path(artifact_dir, pair_id)
    _write_ledger(ledger_path, ledger)
    return ledger_path, ledger
