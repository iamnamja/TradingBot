from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence, TypedDict

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


def _iter_manifest_entries(
    manifest: Mapping[str, Any] | Sequence[Any],
) -> list[dict[str, object]]:
    """
    Normalize manifest into a list of entries understood by _coerce_manifest_task_entry.
    Accepts:
      - {"tasks": ["tasks/001.md", {"path": "..."}]}
      - [{"path": "tasks/001.md"}, "tasks/002.md"]
    """
    if isinstance(manifest, Mapping):
        raw_tasks = manifest.get("tasks") or manifest.get("task_paths") or manifest.get("items") or []
        if isinstance(raw_tasks, (list, tuple)):
            items = list(raw_tasks)
        else:
            items = []
    else:
        items = list(manifest or [])
    normalized: list[dict[str, object]] = []
    for idx, raw in enumerate(items):
        if isinstance(raw, str):
            raw = {"path": raw}
        normalized.append(_coerce_manifest_task_entry(raw, index=idx))
    return normalized


def build_task_queue_from_manifest(
    manifest: Mapping[str, Any] | Sequence[Any],
    repo_root: Path | str = ".",
) -> list[TaskQueueItem]:
    """
    Build a simple in-memory queue from a manifest-like structure.

    This conservative implementation preserves ordering and does not attempt
    to introspect dependencies beyond carrying normalized fields.
    """
    _ = Path(repo_root)  # reserved for future filesystem checks
    entries = _iter_manifest_entries(manifest)
    queue: list[TaskQueueItem] = []
    for ordinal, entry in enumerate(entries, start=1):
        queue.append(
            TaskQueueItem(
                task_path=str(entry.get("task_path") or entry.get("path") or ""),
                ordinal=ordinal,
                project_id="",
                status="queued",
                label=str(entry.get("label") or ""),
                note=str(entry.get("note") or ""),
                stop_policy=str(entry.get("stop_policy") or ""),
                depends_on=tuple(str(p) for p in entry.get("depends_on") or ()),
                blocks=tuple(str(p) for p in entry.get("blocks") or ()),
                deferrable=bool(entry.get("deferrable", False)),
                skipped_by_policy=bool(entry.get("skipped_by_policy", False)),
                rerun_required=bool(entry.get("rerun_required", False)),
            )
        )
    return queue


def _path_exists(repo_root: Path | str, relpath: str) -> bool:
    root = Path(repo_root)
    p = root / relpath
    try:
        return p.exists()
    except Exception:
        return False


def select_single_admissible_safe_task(
    manifest: Mapping[str, Any] | Sequence[Any],
    repo_root: Path | str = ".",
) -> dict[str, object]:
    """
    Conservative selector that only admits a single ready task whose path exists.
    All non-existent paths are treated as blocked to keep the default lane bounded.
    """
    entries = _iter_manifest_entries(manifest)
    ready: list[str] = []
    blocked: list[str] = []
    for entry in entries:
        path = str(entry.get("task_path") or entry.get("path") or "").strip()
        if not path:
            continue
        if _path_exists(repo_root, path):
            ready.append(path)
        else:
            blocked.append(path)
    selected = ready[0] if ready else (entries[0]["task_path"] if entries else "")
    return {
        "default_single_task_path": True,
        "widening_to_multi_task_forbidden": True,
        "selected_task_path": str(selected or ""),
        "ready_task_paths": ready[:1] if ready else [],
        "blocked_task_paths": blocked,
        "reordered": False,
        "note": "Conservative single-task admission: first existing path is selected; others remain blocked.",
    }


# -------------------------
# Two-task pilot admission
# -------------------------

def two_task_readiness_gate_snapshot() -> dict[str, object]:
    """
    Surface a conservative snapshot for bounded two-task pilot admission.
    """
    return {
        "gate_enabled": True,
        "default_single_task_path": True,
        "pilot_ready_verdicts": [
            "ready_to_be_default",
            "conditionally_ready_under_supervision",
        ],
        "bounded_two_task_limit": 2,
        "widening_to_general_multi_task_forbidden": True,
    }


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _promotion_fields(payload: Mapping[str, Any] | None) -> tuple[str, dict, dict]:
    p = dict(payload or {})
    verdict = str(p.get("verdict") or p.get("promotion_verdict") or "").strip()
    metrics = dict(p.get("metrics") or {})
    thresholds = dict(p.get("thresholds") or {})
    return verdict, metrics, thresholds


def _compatibility_regression_flag(payload: Mapping[str, Any] | None) -> bool:
    # Consider both top-level and nested flags
    p = dict(payload or {})
    if "compatibility_regressions" in p:
        return _coerce_bool(p.get("compatibility_regressions"))
    metrics = dict(p.get("metrics") or {})
    if "compatibility_regressions" in metrics:
        return _coerce_bool(metrics.get("compatibility_regressions"))
    # Alternate names
    for key in ("compatibility_regression", "regression_detected"):
        if key in p:
            return _coerce_bool(p.get(key))
        if key in metrics:
            return _coerce_bool(metrics.get(key))
    return False


def _rate_with_threshold(metrics: Mapping[str, Any], thresholds: Mapping[str, Any], *, metric_keys: Iterable[str], threshold_keys: Iterable[str], default_ceiling: float) -> tuple[float, float]:
    rate = 0.0
    for k in metric_keys:
        if k in metrics:
            rate = _coerce_float(metrics.get(k), 0.0)
            break
    ceiling = default_ceiling
    for k in threshold_keys:
        if k in thresholds:
            ceiling = _coerce_float(thresholds.get(k), default_ceiling)
            break
    return rate, ceiling


def evaluate_two_task_readiness_gate(
    *,
    promotion_verdict: str | None = None,
    operator_pilot_flag: bool = False,
    bounded_limit_requested: int | None = None,
    promotion_payload: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """
    Evaluate whether a bounded two-task pilot may be admitted.

    Inputs:
      - operator_pilot_flag: must be True to proceed.
      - promotion_verdict: legacy single string verdict support.
      - promotion_payload: structured promotion object with thresholds/metrics/verdict.

    Conservative rules:
      - An explicit operator flag is required.
      - Verdict must be one of pilot_ready_verdicts.
      - Supervised/escalation rate and unresolved authority-ambiguity rate must be <= configured ceilings.
      - Any compatibility regression blocks admission.
      - Hard cap of 2 tasks is enforced regardless of requested bound.
    """
    snapshot = two_task_readiness_gate_snapshot()
    reasons: list[str] = []
    preconditions: list[str] = []
    allowed = True

    if not bool(operator_pilot_flag):
        preconditions.append("missing_explicit_operator_flag")
        allowed = False

    # Resolve verdict, metrics, thresholds
    pv = str(promotion_verdict or "").strip()
    structured_verdict, metrics, thresholds = _promotion_fields(promotion_payload)
    verdict = structured_verdict or pv
    pilot_ready_verdicts = set(snapshot["pilot_ready_verdicts"])  # type: ignore[arg-type]

    # Compatibility regression check
    if _compatibility_regression_flag(promotion_payload):
        reasons.append("compatibility_regressions_block")
        allowed = False

    # Rate thresholds (tolerant to field names)
    supervised_rate, supervised_ceiling = _rate_with_threshold(
        metrics,
        thresholds,
        metric_keys=("supervised_rate", "escalation_rate", "supervised_or_escalation_rate"),
        threshold_keys=("max_supervised_rate", "max_escalation_rate", "max_supervised_or_escalation_rate"),
        default_ceiling=0.10,
    )
    if supervised_rate > supervised_ceiling:
        reasons.append("supervised_rate_above_threshold")
        allowed = False

    ambig_rate, ambig_ceiling = _rate_with_threshold(
        metrics,
        thresholds,
        metric_keys=("authority_ambiguity_rate", "unresolved_ambiguity_rate", "authority_ambiguity"),
        threshold_keys=("max_authority_ambiguity_rate", "max_unresolved_ambiguity_rate"),
        default_ceiling=0.05,
    )
    if ambig_rate > ambig_ceiling:
        reasons.append("authority_ambiguity_rate_above_threshold")
        allowed = False

    # Verdict check (only after thresholds to accumulate reasons)
    if verdict not in pilot_ready_verdicts:
        reasons.append("verdict_below_threshold")
        allowed = False

    # Hard cap of two tasks
    requested = int(bounded_limit_requested or 0) if bounded_limit_requested is not None else 0
    bounded_limit = 2 if requested <= 0 else min(2, requested)

    return {
        "allowed": bool(allowed and not preconditions),
        "bounded": True,
        "bounded_limit": bounded_limit,
        "preconditions": preconditions,
        "reasons": reasons,
        "evaluation_mode": "structured" if promotion_payload is not None else "verdict_only",
        "eligibility_artifact": {
            "gate_enabled": snapshot["gate_enabled"],
            "pilot_ready_verdicts": list(pilot_ready_verdicts),
            "observed": {
                "verdict": verdict,
                "metrics": metrics,
                "thresholds": thresholds,
                "compatibility_regressions": _compatibility_regression_flag(promotion_payload),
                "supervised_rate": supervised_rate,
                "supervised_rate_ceiling": supervised_ceiling,
                "authority_ambiguity_rate": ambig_rate,
                "authority_ambiguity_ceiling": ambig_ceiling,
            },
            "bounded_limit": bounded_limit,
        },
    }


def plan_two_task_phase_transition(
    *,
    current_phase: str = "single_task_default",
    evaluation: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """
    Convert an evaluation into a conservative phase transition plan.
    """
    ev = dict(evaluation or {})
    allowed = bool(ev.get("allowed", False))
    if not allowed:
        return {
            "transition_allowed": False,
            "current_phase": current_phase,
            "next_phase": current_phase,
            "reason": "two_task_pilot_ineligible",
        }
    return {
        "transition_allowed": True,
        "current_phase": current_phase,
        "next_phase": "two_task_pilot",
        "bounded_limit": int(ev.get("bounded_limit", 2) or 2),
    }

def _proceed_truth_from_result(result: Mapping[str, Any] | None) -> bool | None:
    src = dict(result or {})
    raw = src.get("next_task_may_proceed")
    if isinstance(raw, bool):
        return raw
    text = str(raw or "").strip().lower()
    if not text:
        return None
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return None


def classify_adjacent_task_handoff(
    queue: Sequence[TaskQueueItem],
    *,
    completed_results: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, dict[str, object]]:
    reports: dict[str, dict[str, object]] = {}
    results = dict(completed_results or {})
    by_path = {item.task_path: idx for idx, item in enumerate(queue)}

    for idx, item in enumerate(queue):
        if not item.depends_on:
            continue

        deps = list(item.depends_on)
        dep = deps[0] if deps else ""
        proceed = _proceed_truth_from_result(results.get(dep))

        dependency_present = dep in by_path if dep else False
        adjacent = dependency_present and by_path[dep] == idx - 1 if dep else False

        if not deps:
            handoff_state = "handoff_incomplete"
            reason = "No dependency declared for adjacent handoff."
            may_proceed = False
        elif len(deps) > 1:
            handoff_state = "handoff_incompatible"
            reason = "Multiple dependencies are not supported by the adjacent A->B contract."
            may_proceed = False
        elif proceed is None:
            handoff_state = "handoff_incomplete"
            reason = "Dependency finished without reporting proceed-state truth."
            may_proceed = False
        elif proceed is False:
            handoff_state = "handoff_incompatible"
            reason = "Dependency explicitly blocked progression (next_task_may_proceed=False)."
            may_proceed = False
        else:
            handoff_state = "handoff_ready"
            reason = "Dependency is adjacent and reported proceed-state truth allowing progression."
            may_proceed = True

        reports[item.task_path] = {
            "handoff_state": handoff_state,
            "next_task_may_proceed": may_proceed,
            "depends_on": deps,
            "dependency_present_in_queue": bool(dependency_present),
            "adjacent_in_queue_order": bool(adjacent),
            "implicated_paths": [],
            "verification_authority_profile": "",
            "reason": reason,
        }

    return reports


def adjacent_task_may_start(
    item: TaskQueueItem,
    *,
    queue: Sequence[TaskQueueItem],
    completed_results: Mapping[str, Mapping[str, Any]] | None,
) -> bool:
    reports = classify_adjacent_task_handoff(queue, completed_results=completed_results)
    report = reports.get(item.task_path)
    return bool(report and report.get("handoff_state") == "handoff_ready" and report.get("next_task_may_proceed") is True)
