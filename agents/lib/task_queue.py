from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence, TypedDict

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

    ready: list[TaskQueueItem] = []
    for item in queue:
        if item.task_path in completed or item.status == "completed" or item.skipped_by_policy:
            continue
        missing = [dep for dep in item.depends_on if dep not in completed]
        active_blockers = [
            blocker
            for blocker in reverse_blocks.get(item.task_path, ())
            if blocker not in completed and status_by_path.get(blocker, "queued") != "completed"
        ]
        if missing or active_blockers:
            continue
        ready.append(item)
    return ready


class SafeLaneQueuePlan(TypedDict, total=False):
    decision: str
    selected_task_path: str
    ready_safe_task_paths: list[str]
    supervised_handoff_task_paths: list[str]
    requeue_task_paths: list[str]
    waiting_task_paths: list[str]
    stop_after_selected: bool
    supervised_handoff_required: bool
    rationale: str


class TwoTaskReadinessGateContract(TypedDict, total=False):
    minimum_evaluated_runs: int
    minimum_completion_rate: float
    maximum_escalation_rate: float
    maximum_authority_block_rate: float
    maximum_self_heal_completion_share: float
    require_direct_completions_to_exceed_self_healed_completions: bool


class TwoTaskReadinessGateEvaluation(TypedDict, total=False):
    decision: str
    go_for_bounded_two_task_trials: bool
    current_phase: str
    next_phase_candidate: str
    gate_contract: dict[str, object]
    evaluated_runs: int
    completion_rate: float
    escalation_rate: float
    authority_block_rate: float
    self_heal_completion_share: float
    direct_completion_share: float
    completed_runs: int
    completed_after_retry_runs: int
    direct_completion_runs: int
    thresholds_met: dict[str, bool]
    unmet_gate_reasons: list[str]
    rationale: str


DEFAULT_TWO_TASK_READINESS_GATE: dict[str, object] = {
    "minimum_evaluated_runs": 6,
    "minimum_completion_rate": 0.75,
    "maximum_escalation_rate": 0.25,
    "maximum_authority_block_rate": 0.10,
    "maximum_self_heal_completion_share": 0.34,
    "require_direct_completions_to_exceed_self_healed_completions": True,
}



def _load_scheduler_task_text(
    task_path: str,
    *,
    task_text_loader: Any | None = None,
) -> str:
    if callable(task_text_loader):
        loaded = task_text_loader(task_path)
        return str(loaded or "")
    file_path = Path(task_path)
    if file_path.exists():
        return file_path.read_text(encoding="utf-8", errors="replace")
    return ""



def plan_safe_lane_stop_requeue_policy(
    queue: Sequence[TaskQueueItem],
    *,
    completed_task_paths: Sequence[str] | None = None,
    task_text_loader: Any | None = None,
) -> SafeLaneQueuePlan:
    from agents.lib.task_contracts import evaluate_autonomous_single_task_admission
    from agents.run_task import parse_required_files

    completed = {_normalized_task_path(path) for path in (completed_task_paths or ())}
    ready_items = _ready_queue_items(queue, completed_task_paths=completed_task_paths)

    ready_safe: list[str] = []
    ready_supervised: list[str] = []
    ready_escalation: list[str] = []

    for item in ready_items:
        task_text = _load_scheduler_task_text(item.task_path, task_text_loader=task_text_loader)
        required_paths = list(parse_required_files(task_text))
        autonomous_admission = dict(
            evaluate_autonomous_single_task_admission(
                required_paths,
                task_file=item.task_path,
                task_text=task_text,
            )
        )
        lane = str(autonomous_admission.get("autonomous_single_task_lane", "") or "supervised_only")
        if lane == "autonomous_safe":
            ready_safe.append(item.task_path)
        elif lane == "escalation_required":
            ready_escalation.append(item.task_path)
        else:
            ready_supervised.append(item.task_path)

    handoff_paths = sorted(set(ready_supervised + ready_escalation))
    pending_paths = [
        item.task_path
        for item in queue
        if item.task_path not in completed and item.status != "completed" and not item.skipped_by_policy
    ]

    if len(ready_safe) == 1:
        selected = ready_safe[0]
        requeue = [path for path in pending_paths if path != selected and path not in handoff_paths]
        return {
            "decision": "run_one_and_stop",
            "selected_task_path": selected,
            "ready_safe_task_paths": list(ready_safe),
            "supervised_handoff_task_paths": handoff_paths,
            "requeue_task_paths": requeue,
            "waiting_task_paths": [path for path in pending_paths if path not in ready_safe and path not in handoff_paths],
            "stop_after_selected": True,
            "supervised_handoff_required": bool(handoff_paths),
            "rationale": "Exactly one autonomous-safe task is ready; run it, hand off unsafe ready work, requeue the rest, and stop.",
        }

    if len(ready_safe) > 1:
        requeue = [path for path in pending_paths if path not in handoff_paths]
        return {
            "decision": "stop_and_requeue",
            "selected_task_path": "",
            "ready_safe_task_paths": list(ready_safe),
            "supervised_handoff_task_paths": handoff_paths,
            "requeue_task_paths": requeue,
            "waiting_task_paths": [path for path in pending_paths if path not in ready_safe and path not in handoff_paths],
            "stop_after_selected": True,
            "supervised_handoff_required": bool(handoff_paths),
            "rationale": "More than one autonomous-safe task is ready; the bounded lane refuses widening and requeues remaining safe work.",
        }

    if handoff_paths:
        requeue = [path for path in pending_paths if path not in handoff_paths]
        return {
            "decision": "supervised_handoff_only",
            "selected_task_path": "",
            "ready_safe_task_paths": [],
            "supervised_handoff_task_paths": handoff_paths,
            "requeue_task_paths": requeue,
            "waiting_task_paths": [path for path in pending_paths if path not in handoff_paths],
            "stop_after_selected": True,
            "supervised_handoff_required": True,
            "rationale": "Ready work is supervised-only or escalation-required; no autonomous run is allowed.",
        }

    return {
        "decision": "requeue_waiting",
        "selected_task_path": "",
        "ready_safe_task_paths": [],
        "supervised_handoff_task_paths": [],
        "requeue_task_paths": list(pending_paths),
        "waiting_task_paths": list(pending_paths),
        "stop_after_selected": False,
        "supervised_handoff_required": False,
        "rationale": "No queue item is both ready and safe for autonomous execution yet.",
    }



def select_single_admissible_safe_task(
    queue: Sequence[TaskQueueItem],
    *,
    completed_task_paths: Sequence[str] | None = None,
    task_text_loader: Any | None = None,
) -> dict[str, object]:
    plan = plan_safe_lane_stop_requeue_policy(
        queue,
        completed_task_paths=completed_task_paths,
        task_text_loader=task_text_loader,
    )
    selected_task_path = str(plan.get("selected_task_path", "") or "")
    return {
        "selection_allowed": bool(selected_task_path) and str(plan.get("decision", "")) == "run_one_and_stop",
        "selected_task_path": selected_task_path,
        "selection_decision": str(plan.get("decision", "") or "requeue_waiting"),
        "selection_rationale": str(plan.get("rationale", "") or ""),
        "ready_safe_task_paths": list(plan.get("ready_safe_task_paths", []) or []),
        "supervised_handoff_task_paths": list(plan.get("supervised_handoff_task_paths", []) or []),
    }


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def two_task_readiness_gate_snapshot(
    gate_contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    contract = dict(DEFAULT_TWO_TASK_READINESS_GATE)
    if gate_contract:
        contract.update(dict(gate_contract))
    return {
        "schema_version": 1,
        "current_phase": "phase_a_one_task_execution_quality",
        "next_phase_candidate": "phase_b_bounded_two_task_trials",
        "gate_type": "two_task_readiness",
        "gate_contract": contract,
        "gate_purpose": "Decide whether the bounded external-safe one-task lane has earned the right to start bounded two-task trials.",
        "widening_behavior": "no_immediate_rollout",
    }


def evaluate_two_task_readiness_gate(
    *,
    canary_metrics: Mapping[str, object] | None,
    recovery_report: Mapping[str, object] | None = None,
    gate_contract: Mapping[str, object] | None = None,
) -> TwoTaskReadinessGateEvaluation:
    snapshot = two_task_readiness_gate_snapshot(gate_contract=gate_contract)
    contract = dict(snapshot["gate_contract"])
    metrics = dict(canary_metrics or {})
    recovery = dict(recovery_report or {})

    evaluated_runs = _safe_int(metrics.get("total_runs"), 0)
    completed_runs = _safe_int(metrics.get("completed_runs"), 0)
    completion_rate = _safe_float(metrics.get("completion_rate"), 0.0)

    retry_metrics = dict(metrics.get("retry_metrics", {}) or {})
    completed_after_retry_runs = _safe_int(retry_metrics.get("completed_after_retry_runs"), 0)
    direct_completion_runs = max(completed_runs - completed_after_retry_runs, 0)

    recovery_total_runs = _safe_int(recovery.get("total_runs"), evaluated_runs)
    escalation_required_count = _safe_int(recovery.get("escalation_required_count"), 0)
    escalation_rate = round((escalation_required_count / recovery_total_runs), 4) if recovery_total_runs else 0.0

    authority_block_rate = _safe_float(
        recovery.get("hosted_authority_blocking_frequency", metrics.get("hosted_authority_blocking_frequency", 0.0)),
        0.0,
    )
    self_heal_completion_share = round((completed_after_retry_runs / completed_runs), 4) if completed_runs else 0.0
    direct_completion_share = round((direct_completion_runs / completed_runs), 4) if completed_runs else 0.0

    minimum_evaluated_runs = _safe_int(contract.get("minimum_evaluated_runs"), 6)
    minimum_completion_rate = _safe_float(contract.get("minimum_completion_rate"), 0.75)
    maximum_escalation_rate = _safe_float(contract.get("maximum_escalation_rate"), 0.25)
    maximum_authority_block_rate = _safe_float(contract.get("maximum_authority_block_rate"), 0.10)
    maximum_self_heal_completion_share = _safe_float(contract.get("maximum_self_heal_completion_share"), 0.34)
    require_direct_gt_self_healed = bool(contract.get("require_direct_completions_to_exceed_self_healed_completions", True))

    thresholds_met = {
        "sample_size": evaluated_runs >= minimum_evaluated_runs,
        "completion_rate": completion_rate >= minimum_completion_rate,
        "escalation_rate": escalation_rate <= maximum_escalation_rate,
        "authority_block_rate": authority_block_rate <= maximum_authority_block_rate,
        "self_heal_share": self_heal_completion_share <= maximum_self_heal_completion_share,
        "direct_completions_exceed_self_healed": (direct_completion_runs > completed_after_retry_runs) if require_direct_gt_self_healed else True,
    }

    unmet_gate_reasons: list[str] = []
    if not thresholds_met["sample_size"]:
        unmet_gate_reasons.append(
            f"Need at least {minimum_evaluated_runs} evaluated one-task runs before widening; only {evaluated_runs} are currently measured."
        )
    if not thresholds_met["completion_rate"]:
        unmet_gate_reasons.append(
            f"Completion rate {completion_rate:.4f} is below the required {minimum_completion_rate:.2f} threshold for bounded two-task trials."
        )
    if not thresholds_met["escalation_rate"]:
        unmet_gate_reasons.append(
            f"Escalation rate {escalation_rate:.4f} exceeds the allowed {maximum_escalation_rate:.2f} ceiling."
        )
    if not thresholds_met["authority_block_rate"]:
        unmet_gate_reasons.append(
            f"Hosted-authority block rate {authority_block_rate:.4f} exceeds the allowed {maximum_authority_block_rate:.2f} ceiling."
        )
    if not thresholds_met["self_heal_share"]:
        unmet_gate_reasons.append(
            f"Self-healed completions still account for {self_heal_completion_share:.4f} of completions, above the allowed {maximum_self_heal_completion_share:.2f} share."
        )
    if not thresholds_met["direct_completions_exceed_self_healed"]:
        unmet_gate_reasons.append(
            "Direct completions do not yet exceed self-healed completions, so the repair loop is still too central to successful runs."
        )

    go_for_bounded_two_task_trials = all(bool(v) for v in thresholds_met.values())
    if go_for_bounded_two_task_trials:
        decision = "eligible_for_bounded_two_task_trials"
        rationale = "Measured one-task external-safe results clear the explicit gate, so the repo may begin tightly bounded two-task trials without claiming broader autonomy."
    else:
        decision = "stay_in_bounded_one_task_phase"
        rationale = "The measured one-task lane has not yet cleared the explicit widening gate, so the project should keep improving one-task execution quality before any bounded two-task trials."

    return {
        "decision": decision,
        "go_for_bounded_two_task_trials": go_for_bounded_two_task_trials,
        "current_phase": str(snapshot["current_phase"]),
        "next_phase_candidate": str(snapshot["next_phase_candidate"]),
        "gate_contract": contract,
        "evaluated_runs": evaluated_runs,
        "completion_rate": round(completion_rate, 4),
        "escalation_rate": escalation_rate,
        "authority_block_rate": round(authority_block_rate, 4),
        "self_heal_completion_share": self_heal_completion_share,
        "direct_completion_share": direct_completion_share,
        "completed_runs": completed_runs,
        "completed_after_retry_runs": completed_after_retry_runs,
        "direct_completion_runs": direct_completion_runs,
        "thresholds_met": thresholds_met,
        "unmet_gate_reasons": unmet_gate_reasons,
        "rationale": rationale,
    }


def plan_two_task_phase_transition(
    *,
    canary_metrics: Mapping[str, object] | None,
    recovery_report: Mapping[str, object] | None = None,
    gate_contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    readiness = evaluate_two_task_readiness_gate(
        canary_metrics=canary_metrics,
        recovery_report=recovery_report,
        gate_contract=gate_contract,
    )
    if readiness["go_for_bounded_two_task_trials"]:
        return {
            **readiness,
            "phase_transition_decision": "prepare_bounded_two_task_trials",
            "allowed_ready_safe_task_width": 2,
            "current_safe_lane_width": 1,
        }
    return {
        **readiness,
        "phase_transition_decision": "hold_one_task_lane",
        "allowed_ready_safe_task_width": 1,
        "current_safe_lane_width": 1,
    }


def select_next_task(
    queue: Sequence[TaskQueueItem],
    *,
    completed_task_paths: Sequence[str] | None = None,
) -> TaskQueueItem | None:
    ready = _ready_queue_items(queue, completed_task_paths=completed_task_paths)
    return ready[0] if ready else None

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
