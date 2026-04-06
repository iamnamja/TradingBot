from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence, TypedDict

from agents.lib.controller_contract import (
    BatchPostTaskDecision,
    coerce_post_task_decision,
    is_merge_posture_decision,
    terminal_status_to_post_task_decision,
)

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
    if isinstance(entry, str):
        path = _normalized_task_path(entry)
        if not path:
            raise TaskQueueManifestError(f"Task entry at index {index} is empty.")
        return {
            "path": path,
            "label": "",
            "note": "",
            "stop_policy": "",
            "depends_on": (),
            "blocks": (),
            "deferrable": False,
            "skipped_by_policy": False,
            "rerun_required": False,
        }
    if isinstance(entry, dict):
        path = _normalized_task_path(str(entry.get("path", "")))
        if not path:
            raise TaskQueueManifestError(f"Task entry at index {index} is missing `path`.")
        label = str(entry.get("label", "")).strip()
        note = str(entry.get("note", "")).strip()
        stop_policy = str(entry.get("stop_policy", "")).strip()
        depends_on = _coerce_path_list(entry.get("depends_on"), field_name="depends_on", index=index)
        blocks = _coerce_path_list(entry.get("blocks"), field_name="blocks", index=index)
        deferrable = bool(entry.get("deferrable", entry.get("optional", False)))
        skipped_by_policy = bool(entry.get("skipped_by_policy", entry.get("skip_by_policy", False)))
        rerun_required = bool(entry.get("rerun_required", False))
        return {
            "path": path,
            "label": label,
            "note": note,
            "stop_policy": stop_policy,
            "depends_on": depends_on,
            "blocks": blocks,
            "deferrable": deferrable,
            "skipped_by_policy": skipped_by_policy,
            "rerun_required": rerun_required,
        }
    raise TaskQueueManifestError(f"Task entry at index {index} must be a string path or object with `path`.")



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
    return status == "completed"



def build_task_queue_from_manifest(manifest: dict[str, Any], repo_root: str | Path = ".") -> list[TaskQueueItem]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise TaskQueueManifestError("Manifest must include `tasks` list before queue construction.")
    root = Path(repo_root).resolve()
    entries: list[dict[str, object]] = []
    seen: dict[str, int] = {}
    for idx, raw_entry in enumerate(tasks):
        entry = _coerce_manifest_task_entry(raw_entry, idx)
        path = str(entry["path"])
        if path in seen:
            raise TaskQueueManifestError(f"Duplicate task path in manifest: {path}")
        seen[path] = idx
        if not (root / path).exists():
            raise TaskQueueManifestError(f"Task path does not exist: {path}")
        entries.append(entry)

    all_paths = {str(entry["path"]) for entry in entries}
    for entry in entries:
        path = str(entry["path"])
        depends_on = tuple(str(p) for p in entry["depends_on"])
        blocks = tuple(str(p) for p in entry["blocks"])
        unknown_depends = [p for p in depends_on if p not in all_paths]
        unknown_blocks = [p for p in blocks if p not in all_paths]
        if unknown_depends:
            raise TaskQueueManifestError(f"Task `{path}` depends on missing manifest task(s): {', '.join(unknown_depends)}")
        if unknown_blocks:
            raise TaskQueueManifestError(f"Task `{path}` blocks missing manifest task(s): {', '.join(unknown_blocks)}")
        if path in depends_on:
            raise TaskQueueManifestError(f"Task `{path}` cannot depend on itself.")
        if path in blocks:
            raise TaskQueueManifestError(f"Task `{path}` cannot block itself.")

    return [
        TaskQueueItem(
            task_path=str(entry["path"]),
            ordinal=i + 1,
            label=str(entry["label"]),
            note=str(entry["note"]),
            stop_policy=str(entry["stop_policy"]),
            depends_on=tuple(str(p) for p in entry["depends_on"]),
            blocks=tuple(str(p) for p in entry["blocks"]),
            deferrable=bool(entry["deferrable"]),
            skipped_by_policy=bool(entry["skipped_by_policy"]),
            rerun_required=bool(entry["rerun_required"]),
        )
        for i, entry in enumerate(entries)
    ]



def plan_manifest_progress(queue: Sequence[TaskQueueItem]) -> dict[str, object]:
    from agents.lib.manifest_planner import plan_manifest_progress as _impl

    return dict(_impl(queue))



def choose_next_manifest_task(queue: Sequence[TaskQueueItem]) -> str:
    from agents.lib.manifest_planner import choose_next_manifest_task as _impl

    return str(_impl(queue))



def manifest_planner_snapshot() -> dict[str, object]:
    from agents.lib.manifest_planner import manifest_planner_snapshot as _impl

    return dict(_impl())



def _normalize_batch_outcome(outcome: BatchSummaryTaskOutcome | dict[str, Any]) -> BatchSummaryTaskOutcome:
    task_path = str(outcome.get("task_path", "")).strip()
    status = str(outcome.get("status", outcome.get("terminal_status", "queued"))).strip() or "queued"
    note = str(outcome.get("note", "")).strip()
    raw_decision = str(outcome.get("decision", outcome.get("post_task_decision", ""))).strip()
    if raw_decision:
        decision = coerce_post_task_decision(raw_decision)
    elif status in {"completed", "failed", "manual_patch", "blocked"}:
        decision = terminal_status_to_post_task_decision(status)
    else:
        decision = "stop"
    return {"task_path": task_path, "status": status, "decision": decision, "note": note}



def build_batch_summary_payload(*, manifest_path: str, outcomes: Sequence[BatchSummaryTaskOutcome | dict[str, Any]], final_decision: BatchPostTaskDecision) -> dict[str, object]:
    normalized = [_normalize_batch_outcome(o) for o in outcomes]
    completed = sum(1 for i in normalized if i["status"] == "completed")
    failed = sum(1 for i in normalized if i["status"] == "failed" or is_merge_posture_decision(i["decision"]))
    manual_patch = sum(1 for i in normalized if i["decision"] == "manual_patch")
    blocked = sum(1 for i in normalized if i["decision"] == "blocked")
    return {
        "manifest_path": str(manifest_path),
        "total_tasks": len(normalized),
        "completed_tasks": completed,
        "failed_tasks": failed,
        "manual_patch_tasks": manual_patch,
        "blocked_tasks": blocked,
        "final_batch_decision": final_decision,
        "task_outcomes": normalized,
    }



def render_batch_summary_text(summary: dict[str, object]) -> str:
    return "x"
