from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from builder.orchestrator.benchmark_scorecard import BenchmarkSession as StrictBenchmarkSession


ARTIFACTS_ROOT = Path("artifacts/benchmark")


@dataclass
class BenchmarkTaskTrial:
    task_id: str
    status: str  # completed_direct | completed_after_self_heal | failed | authority_blocked | escalated | manual_intervention
    started_at: str
    ended_at: str
    details: Dict[str, Any]


@dataclass
class BenchmarkSessionArtifact:
    session_id: str
    created_at: str
    tasks: List[BenchmarkTaskTrial]
    summary: Dict[str, int]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: Any) -> None:
    _ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _derive_status_from_result(result: Dict[str, Any]) -> str:
    # Expected fields on result (best-effort, external-safe assumptions):
    # - completed: bool
    # - self_heal_used: bool
    # - authority_blocked: bool
    # - escalated: bool
    completed = bool(result.get("completed"))
    self_heal_used = bool(result.get("self_heal_used"))
    authority_blocked = bool(result.get("authority_blocked"))
    escalated = bool(result.get("escalated"))

    if authority_blocked:
        return "authority_blocked"
    if escalated:
        return "escalated"
    if completed and self_heal_used:
        return "completed_after_self_heal"
    if completed:
        return "completed_direct"
    return "failed"


def _status_flags(status: str) -> Dict[str, bool]:
    return {
        "direct_completion": status == "completed_direct",
        "self_healed_completion": status == "completed_after_self_heal",
        "failed": status == "failed",
        "authority_blocked": status == "authority_blocked",
        "supervised": status == "escalated",
        "manual_edit": status == "manual_intervention",
    }


def run_one_task_external_safe_benchmark(
    tasks: Iterable[Dict[str, Any]],
    select: Optional[Iterable[str]] = None,
    artifacts_root: Optional[Path] = None,
    executor: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    manual_intervention: bool = False,
) -> BenchmarkSessionArtifact:
    """
    External-safe one-task benchmark harness.

    - tasks: iterable of task specs, each having at least an "id" field (string).
    - select: optional iterable of task ids to include; if None, include all provided tasks.
    - artifacts_root: where to write session artifacts; defaults to ARTIFACTS_ROOT/sessions/<session_id>.
    - executor: callable that runs a single task spec and returns a result dict. If None, tasks are marked failed.
    - manual_intervention: if True, mark trials as failed due to manual intervention (autonomy broken).

    Returns: BenchmarkSessionArtifact with machine-readable summary and per-task trials.
    """
    session_id = str(uuid.uuid4())
    created_at = _utc_now_iso()

    # Task selection
    selected_ids: Optional[set[str]] = set(select) if select is not None else None
    task_list: List[Dict[str, Any]] = []
    for t in tasks:
        tid = str(t.get("id") or t.get("task_id") or "")
        if not tid:
            # Skip specs without an identifier to keep external-safe behavior deterministic
            continue
        if selected_ids is not None and tid not in selected_ids:
            continue
        task_list.append({**t, "id": tid})

    # Prepare artifact paths
    root = artifacts_root or ARTIFACTS_ROOT / "sessions" / session_id
    root = Path(root)
    _ensure_dir(root)

    trials: List[BenchmarkTaskTrial] = []
    summary_counts: Dict[str, int] = {
        "completed_direct": 0,
        "completed_after_self_heal": 0,
        "failed": 0,
        "authority_blocked": 0,
        "escalated": 0,
        "manual_intervention": 0,
    }

    for spec in task_list:
        tid = spec["id"]
        started_at = _utc_now_iso()

        if manual_intervention:
            status = "manual_intervention"
            result: Dict[str, Any] = {"completed": False, "manual_intervention": True}
        elif executor is None:
            # No executor provided; record as failed without execution
            status = "failed"
            result = {"completed": False}
        else:
            # Execute task through provided bounded one-task runner callable
            try:
                raw = executor(spec)
                result = dict(raw) if isinstance(raw, dict) else {}
            except Exception as exc:  # defensive external-safe execution
                result = {"completed": False, "error": f"{type(exc).__name__}: {exc}"}
            status = _derive_status_from_result(result)

        ended_at = _utc_now_iso()

        # Record trial
        trials.append(
            BenchmarkTaskTrial(
                task_id=tid,
                status=status,
                started_at=started_at,
                ended_at=ended_at,
                details=result,
            )
        )
        if status in summary_counts:
            summary_counts[status] += 1
        else:
            summary_counts["failed"] += 1  # unknown -> failed (conservative)

    # Build session artifact
    session = BenchmarkSessionArtifact(
        session_id=session_id,
        created_at=created_at,
        tasks=trials,
        summary={"total": len(trials), **summary_counts},
    )

    # Persist strict integrated scorecard and promotion artifacts
    strict_session = StrictBenchmarkSession(root)
    # Ensure live-session integration records results deterministically
    for result in session.tasks:
        flags = _status_flags(result.status)
        strict_session.record_run(
            direct_completion=flags["direct_completion"],
            self_healed_completion=flags["self_healed_completion"],
            failed=flags["failed"],
            authority_blocked=flags["authority_blocked"],
            supervised=flags["supervised"],
            manual_edit=flags["manual_edit"],
        )
    strict_session.close()

    # Persist a human-readable session.json summary for reference
    _write_json(root / "session.json", {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "summary": session.summary,
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status,
                "started_at": t.started_at,
                "ended_at": t.ended_at,
                "details": t.details,
            }
            for t in session.tasks
        ],
    })

    return session


def run_two_task_canary_benchmark(
    tasks: Iterable[Dict[str, Any]],
    artifacts_root: Optional[Path] = None,
    executor: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run a bounded two-task canary pilot benchmark.

    Writes only canary_* artifacts alongside the strict one-task artifacts:
    - canary_trials.json
    - canary_scorecard.json
    - canary_promotion.json

    Returns a metrics dict.
    """
    # Prepare artifact root
    root = Path(artifacts_root or ARTIFACTS_ROOT / "canary_sessions" / str(uuid.uuid4()))
    _ensure_dir(root)

    # Normalize task ids
    task_list: List[Dict[str, Any]] = []
    for t in tasks:
        tid = str(t.get("id") or t.get("task_id") or "")
        if tid:
            task_list.append({**t, "id": tid})

    trials: List[Dict[str, Any]] = []
    metrics = {
        "total": 0,
        "pilot_attempts": 0,
        "ineligible_attempts": 0,
        "admissions_blocked": 0,
        "pilot_completions": 0,
        "handoff_incomplete_failures": 0,
        "handoff_incompatible_failures": 0,
        "supervised_interventions": 0,
    }

    for spec in task_list:
        tid = spec["id"]
        metrics["total"] += 1
        if executor is None:
            rec = {
                "task_id": tid,
                "eligible_for_pilot": False,
                "admitted": False,
                "blocked_admission": False,
                "completed": False,
                "handoff_status": "",
                "supervised": False,
            }
        else:
            try:
                r = executor(spec)
            except Exception as exc:
                r = {
                    "eligible_for_pilot": False,
                    "admitted": False,
                    "blocked_admission": False,
                    "completed": False,
                    "handoff_status": "",
                    "supervised": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            rec = {
                "task_id": tid,
                "eligible_for_pilot": bool(r.get("eligible_for_pilot", False)),
                "admitted": bool(r.get("admitted", False)),
                "blocked_admission": bool(r.get("blocked_admission", False)),
                "completed": bool(r.get("completed", False)),
                "handoff_status": str(r.get("handoff_status", "")),
                "supervised": bool(r.get("supervised", False)),
            }

        trials.append(rec)

        if not rec["eligible_for_pilot"]:
            metrics["ineligible_attempts"] += 1
            continue

        metrics["pilot_attempts"] += 1
        if rec["blocked_admission"] and not rec["admitted"]:
            metrics["admissions_blocked"] += 1
        if rec["supervised"]:
            metrics["supervised_interventions"] += 1
        if rec["admitted"] and rec["completed"]:
            metrics["pilot_completions"] += 1
        elif rec["admitted"] and not rec["completed"]:
            if rec["handoff_status"] == "incomplete":
                metrics["handoff_incomplete_failures"] += 1
            if rec["handoff_status"] == "incompatible":
                metrics["handoff_incompatible_failures"] += 1

    # Persist canary artifacts
    _write_json(root / "canary_trials.json", trials)
    canary_scorecard = {
        "created_at": _utc_now_iso(),
        "metrics": metrics,
        "notes": "Two-task canary metrics derived from pilot attempts. Strict one-task artifacts remain untouched.",
    }
    _write_json(root / "canary_scorecard.json", canary_scorecard)

    # Conservative pilot verdict
    thresholds = {
        "min_pilot_attempts": 1,
        "min_pilot_completions": 1,
        "max_supervised_intervention_rate": 1.0,  # supervision is expected in pilot; keep conservative but permissive
    }
    attempts = metrics["pilot_attempts"]
    completions = metrics["pilot_completions"]
    supervised_rate = (metrics["supervised_interventions"] / attempts) if attempts else 0.0

    if attempts < thresholds["min_pilot_attempts"]:
        verdict = "not_ready_for_pilot"
    elif completions >= thresholds["min_pilot_completions"] and supervised_rate <= thresholds["max_supervised_intervention_rate"]:
        verdict = "ready_for_bounded_supervised_pilot"
    else:
        verdict = "conditionally_ready_under_supervision"

    promotion = {
        "created_at": _utc_now_iso(),
        "thresholds": thresholds,
        "metrics": metrics,
        "verdict": verdict,
    }
    _write_json(root / "canary_promotion.json", promotion)

    return metrics
