from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence, TypedDict

from agents.lib.controller_contract import (
    BatchPostTaskDecision as _CC_BatchPostTaskDecision,
    terminal_status_to_post_task_decision,
)
from agents.lib.manifest_planner import normalize_manifest_entry_schema

# Re-export for contract parity with tests
BatchPostTaskDecision = _CC_BatchPostTaskDecision

QueueStatus = Literal["queued", "running", "completed", "blocked", "failed", "manual_patch"]


class PostTaskSignals(TypedDict, total=False):
    validator_ok: bool
    deliverable_complete: bool
    protected_lane_ok: bool
    duplicate_bundle_conflict: bool
    manual_patch_recommended: bool


class BatchSummaryTaskOutcome(TypedDict, total=False):
    task_path: str
    status: QueueStatus
    decision: BatchPostTaskDecision
    note: str


ALLOWED_STATUS_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "queued": ("running",),
    "running": ("completed", "failed", "manual_patch", "blocked"),
    "completed": (),
    "failed": (),
    "manual_patch": (),
    "blocked": (),
}


class TaskQueueManifestError(ValueError):
    """Raised when a task-list manifest is invalid."""


class TaskQueueTransitionError(ValueError):
    """Raised when a queue item status transition is invalid."""


@dataclass(frozen=True)
class TaskQueueItem:
    task_path: str
    ordinal: int
    project_id: str = ""
    status: QueueStatus = "queued"
    status_note: str = ""
    label: str = ""
    note: str = ""
    stop_policy: str = ""
    depends_on: tuple[str, ...] = ()
    blocks: tuple[str, ...] = ()
    deferrable: bool = False
    skipped_by_policy: bool = False
    rerun_required: bool = False


def _normalized_task_path(raw_path: str) -> str:
    return raw_path.strip().replace("\\", "/")


def _coerce_path_list(raw_value: Any, *, field_name: str, index: int) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    if not isinstance(raw_value, (list, tuple)):
        raise TaskQueueManifestError(f"Task entry at index {index} field `{field_name}` must be a list of paths.")
    normalized: list[str] = []
    for raw in raw_value:
        path = _normalized_task_path(str(raw))
        if not path:
            raise TaskQueueManifestError(f"Task entry at index {index} field `{field_name}` contains empty path.")
        normalized.append(path)
    return tuple(normalized)


def _coerce_manifest_task_entry(entry: Any, index: int) -> dict[str, object]:
    try:
        normalized = normalize_manifest_entry_schema(entry, index=index)
    except ValueError as exc:
        raise TaskQueueManifestError(str(exc)) from exc
    return {
        "path": str(normalized["path"]),
        "task_path": str(normalized["task_path"]),
        "task_id": str(normalized["task_id"]),
        "label": str(normalized["label"]),
        "note": str(normalized["note"]),
        "stop_policy": str(normalized["stop_policy"]),
        "depends_on": tuple(str(p) for p in normalized["depends_on"]),
        "blocks": tuple(str(p) for p in normalized["blocks"]),
        "deferrable": bool(normalized["deferrable"]),
        "skipped_by_policy": bool(normalized["skipped_by_policy"]),
        "rerun_required": bool(normalized["rerun_required"]),
    }


def validate_queue_status_transition(from_status: QueueStatus, to_status: QueueStatus) -> None:
    allowed = ALLOWED_STATUS_TRANSITIONS.get(from_status, ())
    if to_status not in allowed:
        raise TaskQueueTransitionError(f"Invalid queue status transition: {from_status} -> {to_status}.")


def queue_signature(queue: list[TaskQueueItem]) -> tuple[str, ...]:
    return tuple(item.task_path for item in queue)


def decide_post_task_action(status: QueueStatus, *, signals: PostTaskSignals | None = None) -> BatchPostTaskDecision:
    s = signals or {}
    if s.get("duplicate_bundle_conflict", False):
        return "blocked"
    if status == "blocked":
        return "blocked"
    if status == "manual_patch" or s.get("manual_patch_recommended", False):
        return "manual_patch"
    if not s.get("deliverable_complete", True):
        return "stop"
    if not s.get("protected_lane_ok", True):
        return "stop"
    if not s.get("validator_ok", True):
        return "stop"
    return terminal_status_to_post_task_decision(status)


def may_proceed_to_next_task(status: QueueStatus) -> bool:
    return decide_post_task_action(status) == "continue"


def build_task_queue_from_manifest(
    manifest: Mapping[str, Any] | Sequence[Any],
    repo_root: Path | str = ".",
) -> list[TaskQueueItem]:
    """
    Construct a deterministic queue of TaskQueueItem entries from a manifest.

    - Accepts either a mapping with a "tasks" list or a raw sequence of task entries.
    - Normalizes per-entry schema using manifest_planner.normalize_manifest_entry_schema(...)
    - Ordinals start from 1 preserving input order.
    """
    root = Path(repo_root)
    if isinstance(manifest, Mapping):
        raw_tasks = manifest.get("tasks") or []
    else:
        raw_tasks = manifest

    entries: list[dict[str, object]] = []
    for idx, raw in enumerate(raw_tasks):
        entries.append(_coerce_manifest_task_entry(raw, idx))

    queue: list[TaskQueueItem] = []
    for i, e in enumerate(entries, start=1):
        task_path = _normalized_task_path(str(e["task_path"]))
        # Normalize relative to repo_root for consistency but keep stored path as provided
        _ = (root / task_path)  # path object not used directly; consistency placeholder
        item = TaskQueueItem(
            task_path=task_path,
            ordinal=i,
            label=str(e.get("label") or ""),
            note=str(e.get("note") or ""),
            stop_policy=str(e.get("stop_policy") or ""),
            depends_on=tuple(e.get("depends_on") or ()),
            blocks=tuple(e.get("blocks") or ()),
            deferrable=bool(e.get("deferrable", False)),
            skipped_by_policy=bool(e.get("skipped_by_policy", False)),
            rerun_required=bool(e.get("rerun_required", False)),
        )
        queue.append(item)
    return queue


def select_single_admissible_safe_task(
    manifest: Mapping[str, Any] | Sequence[Any],
    repo_root: Path | str = ".",
) -> dict[str, object]:
    """
    Recommend a single admissible task path for the default one-task orchestrator lane.

    Behavior:
    - Picks the first existing manifest task file under repo_root.
    - Reports ready_task_paths (existing), blocked_task_paths (non-existent), and selected_task_path (if any).
    - Explicitly forbids widening to multi-task autonomy.
    """
    root = Path(repo_root)
    if isinstance(manifest, Mapping):
        raw = manifest.get("tasks") or []
    else:
        raw = manifest

    ready: list[str] = []
    blocked: list[str] = []

    for entry in raw:
        normalized = _coerce_manifest_task_entry(entry, 0)
        path = _normalized_task_path(str(normalized["task_path"]))
        disk = (root / path).resolve()
        if disk.exists() and disk.is_file():
            ready.append(path)
        else:
            blocked.append(path)

    selected = ready[0] if ready else ""
    return {
        "default_single_task_path": True,
        "widening_to_multi_task_forbidden": True,
        "selected_task_path": selected,
        "ready_task_paths": list(ready if selected else [] if not ready else [selected]),
        "blocked_task_paths": list(blocked),
        "reordered": False,
        "reason": "" if selected else "no_existing_task_found",
    }


def two_task_readiness_gate_snapshot() -> dict[str, object]:
    """
    Snapshot of the explicit two-task pilot gate policy.
    """
    return {
        "gate_enabled": True,
        "default_single_task_path": True,
        "pilot_ready_verdicts": ("ready_to_be_default", "conditionally_ready_under_supervision"),
        "explicit_operator_flag_required": True,
        "bounded_two_task_limit": 2,
        "widening_to_general_multi_task_forbidden": True,
    }


def evaluate_two_task_readiness_gate(
    *,
    promotion_verdict: str,
    operator_pilot_flag: bool,
    bounded_limit_requested: int | None = None,
) -> dict[str, object]:
    """
    Evaluate preconditions for a bounded two-task pilot.

    Preconditions:
    - promotion_verdict in {"ready_to_be_default", "conditionally_ready_under_supervision"}
    - operator_pilot_flag must be True
    - bounded limit hard-capped to 2
    """
    snap = two_task_readiness_gate_snapshot()
    allowed_verdicts = set(snap["pilot_ready_verdicts"])  # type: ignore[index]
    preconditions: list[str] = []
    allowed = True

    if promotion_verdict not in allowed_verdicts:
        preconditions.append("insufficient_promotion_verdict")
        allowed = False
    if not operator_pilot_flag:
        preconditions.append("missing_explicit_operator_flag")
        allowed = False

    limit_cap = int(snap["bounded_two_task_limit"])  # type: ignore[arg-type]
    requested = int(bounded_limit_requested or limit_cap)
    bounded_limit = min(limit_cap, max(1, requested))

    reason = (
        ""
        if allowed
        else "Preconditions not met for two-task pilot: " + ", ".join(preconditions)
    )

    return {
        "allowed": bool(allowed),
        "bounded": True,
        "bounded_limit": bounded_limit,
        "preconditions": preconditions,
        "reason": reason,
    }


def plan_two_task_phase_transition(
    *,
    current_phase: str,
    evaluation: Mapping[str, Any],
) -> dict[str, object]:
    """
    Compute conservative phase transition based on evaluation.

    - From 'single_task_default' -> 'two_task_pilot' when evaluation.allowed is True.
    - Otherwise, remain in current phase.
    """
    allowed = bool(evaluation.get("allowed", False))
    if current_phase == "single_task_default" and allowed:
        return {
            "transition_allowed": True,
            "next_phase": "two_task_pilot",
            "bounded_limit": int(evaluation.get("bounded_limit", 2) or 2),
        }
    return {
        "transition_allowed": False,
        "next_phase": current_phase,
    }
