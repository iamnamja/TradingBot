from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


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
            # The executor must be external-safe and single-task bounded.
            try:
                result = executor(spec) or {}
            except Exception as exc:  # external-safe: catch and record
                result = {"completed": False, "error": str(exc)}
            status = _derive_status_from_result(result)

        ended_at = _utc_now_iso()

        trial = BenchmarkTaskTrial(
            task_id=tid,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            details=result,
        )
        trials.append(trial)
        summary_counts[status] = summary_counts.get(status, 0) + 1

        # Write per-task artifact
        _write_json(root / f"{tid}.json", asdict(trial))

    session = BenchmarkSessionArtifact(
        session_id=session_id,
        created_at=created_at,
        tasks=trials,
        summary=summary_counts,
    )

    # Write session artifact
    _write_json(root / "session.json", asdict(session))
    return session
