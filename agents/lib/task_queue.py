from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence, TypedDict

from agents.lib.controller_contract import (
    BatchPostTaskDecision,
    coerce_post_task_decision,
    is_merge_posture_decision,
    terminal_status_to_post_task_decision,
)
from agents.lib.manifest_planner import normalize_manifest_entry_schema

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


class SingleTaskSchedulerBridgeDecision(TypedDict, total=False):
    bridge_decision: str
    rationale: str
    selected_task_path: str
    ready_task_paths: list[str]
    safe_ready_task_paths: list[str]
    non_safe_ready_task_paths: list[str]
    admission: dict[str, object]
    proof_admission: dict[str, object]


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
    return status == "completed"



def build_task_queue_from_manifest(manifest: dict[str, Any], repo_root: str | Path = ".", dependency_graph: Mapping[str, Sequence[str]] | None = None) -> list[TaskQueueItem]:
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
        if dependency_graph is None and not (root / path).exists():
            raise TaskQueueManifestError(f"Task path does not exist: {path}")
        entries.append(entry)

    if dependency_graph:
        normalized_graph = {
            _normalized_task_path(str(task_path)): tuple(_normalized_task_path(str(dep)) for dep in deps)
            for task_path, deps in dict(dependency_graph).items()
        }
        for entry in entries:
            task_path = str(entry["path"])
            if task_path in normalized_graph:
                entry["depends_on"] = tuple(dep for dep in normalized_graph[task_path] if dep)

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
            task_path=str(entry.get("task_path") or entry["path"]),
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





def select_next_task(
    queue: Sequence[TaskQueueItem],
    *,
    completed_task_paths: Sequence[str] | None = None,
) -> TaskQueueItem | None:
    ready_items = _ready_queue_items(queue, completed_task_paths=completed_task_paths)
    return ready_items[0] if ready_items else None

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


def _task_is_dependency_ready(
    item: TaskQueueItem,
    *,
    completed: set[str],
    status_by_path: Mapping[str, str],
    reverse_blocks: Mapping[str, tuple[str, ...]],
) -> bool:
    if item.task_path in completed or item.status == "completed" or item.skipped_by_policy:
        return False
    missing = [dep for dep in item.depends_on if dep not in completed]
    active_blockers = [
        blocker
        for blocker in reverse_blocks.get(item.task_path, ())
        if blocker not in completed and status_by_path.get(blocker, "queued") != "completed"
    ]
    return not missing and not active_blockers


def _ready_queue_items(
    queue: Sequence[TaskQueueItem],
    *,
    completed_task_paths: Sequence[str] | None = None,
) -> list[TaskQueueItem]:
    completed = {_normalized_task_path(path) for path in (completed_task_paths or ())}
    status_by_path = {item.task_path: ("completed" if item.task_path in completed else item.status) for item in queue}
    reverse_blocks: dict[str, tuple[str, ...]] = {}
    for item in queue:
        for blocked in item.blocks:
            reverse_blocks.setdefault(blocked, tuple())
            reverse_blocks[blocked] = tuple(sorted(set(reverse_blocks[blocked]) | {item.task_path}))
    return [
        item
        for item in queue
        if _task_is_dependency_ready(
            item,
            completed=completed,
            status_by_path=status_by_path,
            reverse_blocks=reverse_blocks,
        )
    ]


def select_single_admissible_safe_task(
    queue: Sequence[TaskQueueItem],
    *,
    repo_root: str | Path = ".",
    completed_task_paths: Sequence[str] | None = None,
    admission_evaluator: Callable[[TaskQueueItem, Path], Mapping[str, object]] | None = None,
) -> SingleTaskSchedulerBridgeDecision:
    ready_items = _ready_queue_items(queue, completed_task_paths=completed_task_paths)
    if not ready_items:
        return {
            "bridge_decision": "no_ready_task",
            "rationale": "No dependency-ready task is currently available for the bounded single-task lane.",
            "ready_task_paths": [],
            "safe_ready_task_paths": [],
            "non_safe_ready_task_paths": [],
        }

    root = Path(repo_root).resolve()

    def _default_evaluator(item: TaskQueueItem, resolved_root: Path) -> Mapping[str, object]:
        from agents import run_task as _run_task  # type: ignore

        task_file = resolved_root / item.task_path
        task_text = task_file.read_text(encoding="utf-8", errors="replace")
        required_paths = list(_run_task.parse_required_files(task_text))
        admission = dict(
            _run_task.evaluate_autonomous_single_task_admission(
                required_paths,
                task_file=item.task_path,
                task_text=task_text,
            )
        )
        proof_admission = dict(
            _run_task.evaluate_proof_task_admission(
                task_text=task_text,
                task_file=item.task_path,
                required_paths=required_paths,
            )
        )
        return {
            "task_path": item.task_path,
            "required_paths": required_paths,
            "admission": admission,
            "proof_admission": proof_admission,
        }

    evaluator = admission_evaluator or _default_evaluator
    safe_candidates: list[dict[str, object]] = []
    non_safe_ready: list[str] = []

    for item in ready_items:
        evaluation = dict(evaluator(item, root))
        admission = dict(evaluation.get("admission", {}) or {})
        proof_admission = dict(evaluation.get("proof_admission", {}) or {})
        allowed = bool(admission.get("autonomous_single_task_allowed", False)) and bool(
            proof_admission.get("proof_task_admission_allowed", False)
        )
        record = {
            "task_path": item.task_path,
            "admission": admission,
            "proof_admission": proof_admission,
        }
        if allowed:
            safe_candidates.append(record)
        else:
            non_safe_ready.append(item.task_path)

    if len(safe_candidates) != 1:
        rationale = (
            "Scheduler bridge refuses to widen into multi-task autonomous execution because more than one "
            "dependency-ready safe task is admissible."
            if len(safe_candidates) > 1
            else "Scheduler bridge found no dependency-ready task that is admissible for the bounded safe lane."
        )
        return {
            "bridge_decision": "delegate_to_supervision",
            "rationale": rationale,
            "ready_task_paths": [item.task_path for item in ready_items],
            "safe_ready_task_paths": [str(candidate["task_path"]) for candidate in safe_candidates],
            "non_safe_ready_task_paths": non_safe_ready,
        }

    selected = safe_candidates[0]
    return {
        "bridge_decision": "delegate_to_single_task_runner",
        "rationale": "Exactly one dependency-ready safe task is admissible, so scheduler routing may invoke the bounded single-task runner.",
        "selected_task_path": str(selected["task_path"]),
        "ready_task_paths": [item.task_path for item in ready_items],
        "safe_ready_task_paths": [str(selected["task_path"])],
        "non_safe_ready_task_paths": non_safe_ready,
        "admission": dict(selected["admission"]),
        "proof_admission": dict(selected["proof_admission"]),
    }
