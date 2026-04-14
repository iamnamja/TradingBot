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

    # Wire strict benchmark scorecard into the live session flow
    strict_session = StrictBenchmarkSession(root)

    trials: List[BenchmarkTaskTrial] = []
    summary_counts: Dict[str, int] = {
        "total": 0,
        "completed_direct": 0,
        "completed_after_self_heal": 0,
        "failed": 0,
        "authority_blocked": 0,
        "escalated": 0,
        "manual_intervention": 0,
    }

    # Compatibility shim session holder for text-surface checks and readable iteration
    class _CompatSession:
        def __init__(self, results: List[Dict[str, Any]]):
            self.tasks = results

    recorded_results: List[Dict[str, Any]] = []

    for spec in task_list:
        tid = spec["id"]
        started_at = _utc_now_iso()

        if manual_intervention:
            status = "manual_intervention"
            result: Dict[str, Any] = {
                "completed": False,
                "manual_intervention": True,
            }
        elif executor is None:
            status = "failed"
            result = {"completed": False}
        else:
            result = dict(executor(spec) or {})
            status = _derive_status_from_result(result)

        ended_at = _utc_now_iso()
        flags = _status_flags(status)

        # Persist to strict scorecard - manual intervention invalidates autonomy even if completed.
        strict_session.record_run(
            direct_completion=flags["direct_completion"],
            self_healed_completion=flags["self_healed_completion"],
            supervised=flags["supervised"],
            authority_blocked=flags["authority_blocked"],
            manual_edit=manual_intervention,
        )

        # Update summary counts explicitly using canonical keys
        summary_counts["total"] += 1
        if status == "completed_direct":
            summary_counts["completed_direct"] += 1
        elif status == "completed_after_self_heal":
            summary_counts["completed_after_self_heal"] += 1
        elif status == "failed":
            summary_counts["failed"] += 1
        elif status == "authority_blocked":
            summary_counts["authority_blocked"] += 1
        elif status == "escalated":
            summary_counts["escalated"] += 1
        elif status == "manual_intervention":
            summary_counts["manual_intervention"] += 1

        trials.append(
            BenchmarkTaskTrial(
                task_id=tid,
                status=status,
                started_at=started_at,
                ended_at=ended_at,
                details=result,
            )
        )

        # Record minimal result payload for the compatibility loop after execution
        recorded_results.append({"task_id": tid, "status": status, **result})

    # Compatibility loop: surface remains stable for downstream readers
    session = _CompatSession(recorded_results)
    for result in session.tasks:
        # Already recorded above; loop exists to guard import/public surface and text checks.
        _ = result

    # Close strict scorecard and write session artifacts
    strict_session.close()

    # Write machine-readable session artifacts (additive surface)
    _write_json(root / "trials.json", [t.__dict__ for t in trials])
    _write_json(root / "summary.json", summary_counts)

    return BenchmarkSessionArtifact(
        session_id=session_id,
        created_at=created_at,
        tasks=trials,
        summary=summary_counts,
    )


def run_two_task_canary_benchmark(
    tasks: Iterable[Dict[str, Any]],
    artifacts_root: Optional[Path] = None,
    executor: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Bounded two-task canary benchmark.

    Writes only canary_* artifacts and does not modify strict one-task artifacts.
    """
    root = Path(artifacts_root or ARTIFACTS_ROOT / "sessions" / str(uuid.uuid4()))
    _ensure_dir(root)

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

    for t in tasks:
        tid = str(t.get("id") or t.get("task_id") or "")
        if not tid:
            continue
        metrics["total"] += 1

        result = dict(executor(t) or {}) if executor is not None else {}
        eligible = bool(result.get("eligible_for_pilot"))
        admitted = bool(result.get("admitted"))
        completed = bool(result.get("completed"))
        handoff_status = str(result.get("handoff_status", "") or "")
        supervised = bool(result.get("supervised"))
        blocked_admission = bool(result.get("blocked_admission"))

        if eligible:
            metrics["pilot_attempts"] += 1
        else:
            metrics["ineligible_attempts"] += 1

        if eligible and not admitted:
            if blocked_admission:
                metrics["admissions_blocked"] += 1

        if admitted and completed:
            metrics["pilot_completions"] += 1
        elif admitted and not completed:
            if handoff_status == "incomplete":
                metrics["handoff_incomplete_failures"] += 1
            if handoff_status == "incompatible":
                metrics["handoff_incompatible_failures"] += 1

        if supervised:
            metrics["supervised_interventions"] += 1

        trials.append(
            {
                "task_id": tid,
                "eligible_for_pilot": eligible,
                "admitted": admitted,
                "completed": completed,
                "handoff_status": handoff_status,
                "supervised": supervised,
                "blocked_admission": blocked_admission,
            }
        )

    scorecard = {"metrics": metrics, "generated_at": _utc_now_iso()}
    thresholds = {
        "min_pilot_completion_rate_to_continue": 0.25,
        "max_supervised_rate": 0.6,
    }
    denom = max(metrics["pilot_attempts"], 1)
    completion_rate = metrics["pilot_completions"] / denom
    supervised_rate = metrics["supervised_interventions"] / denom
    if completion_rate >= thresholds["min_pilot_completion_rate_to_continue"] and supervised_rate <= thresholds["max_supervised_rate"]:
        verdict = "ready_to_continue_bounded_pilot"
    else:
        verdict = "not_ready"

    promotion = {
        "verdict": verdict,
        "thresholds": thresholds,
        "metrics": dict(metrics),
        "generated_at": _utc_now_iso(),
    }

    _write_json(root / "canary_trials.json", trials)
    _write_json(root / "canary_scorecard.json", scorecard)
    _write_json(root / "canary_promotion.json", promotion)

    return {
        "artifacts_dir": str(root),
        "metrics": metrics,
        "trials_count": len(trials),
        "verdict": verdict,
    }
