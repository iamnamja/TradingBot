from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

@dataclass(frozen=True)
class ManifestPlannerSnapshot:
    dependency_surface_enabled: bool = True
    supports_depends_on: bool = True
    supports_blocks: bool = True
    supports_deferrable: bool = True
    supports_skipped_by_policy: bool = True
    supports_rerun_required: bool = True
    supports_task_admission: bool = True
    supports_bounded_decomposition: bool = True
    supports_backlog_intake: bool = True
    supports_explicit_next_task_selection_policy: bool = True
    supports_priority_signal: bool = True
    supports_authority_prerequisite_signal: bool = True
    supports_carry_forward_memory_input: bool = True
    conservative_reordering_only: bool = True




@dataclass(frozen=True)
class TaskDecompositionTruth:
    decomposition_status: str = "not_required"
    bounded_decomposition_required: bool = False
    decomposition_unit_count: int = 0
    decomposition_summary: str = ""
    decomposition_units: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "decomposition_status": self.decomposition_status,
            "bounded_decomposition_required": self.bounded_decomposition_required,
            "decomposition_unit_count": self.decomposition_unit_count,
            "decomposition_summary": self.decomposition_summary,
            "decomposition_units": [
                {"label": label, "task_paths": list(paths)}
                for label, paths in self.decomposition_units
            ],
        }


@dataclass(frozen=True)
class ManifestPlannerTruth:
    selected_task_path: str = ""
    reordered: bool = False
    ready_task_paths: tuple[str, ...] = ()
    blocked_task_paths: tuple[str, ...] = ()
    deferred_task_paths: tuple[str, ...] = ()
    skipped_task_paths: tuple[str, ...] = ()
    rerun_required_task_paths: tuple[str, ...] = ()
    blocking_reasons: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_task_path": self.selected_task_path,
            "reordered": self.reordered,
            "ready_task_paths": list(self.ready_task_paths),
            "blocked_task_paths": list(self.blocked_task_paths),
            "deferred_task_paths": list(self.deferred_task_paths),
            "skipped_task_paths": list(self.skipped_task_paths),
            "rerun_required_task_paths": list(self.rerun_required_task_paths),
            "blocking_reasons": {task_path: reason for task_path, reason in self.blocking_reasons},
        }


@dataclass(frozen=True)
class DependencyGraphTruth:
    dependency_nodes: tuple[str, ...] = ()
    dependency_edges: tuple[tuple[str, str], ...] = ()
    blocking_edges: tuple[tuple[str, str], ...] = ()
    unresolved_dependencies: tuple[tuple[str, tuple[str, ...]], ...] = ()
    blocked_by_dependencies: tuple[str, ...] = ()
    decomposition_required_task_paths: tuple[str, ...] = ()
    decomposition_manual_only_task_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "dependency_nodes": list(self.dependency_nodes),
            "dependency_edges": [
                {"from": source, "to": target}
                for source, target in self.dependency_edges
            ],
            "blocking_edges": [
                {"from": source, "to": target}
                for source, target in self.blocking_edges
            ],
            "unresolved_dependencies": {
                task_path: list(deps)
                for task_path, deps in self.unresolved_dependencies
            },
            "blocked_by_dependencies": list(self.blocked_by_dependencies),
            "decomposition_required_task_paths": list(self.decomposition_required_task_paths),
            "decomposition_manual_only_task_paths": list(self.decomposition_manual_only_task_paths),
        }


@dataclass(frozen=True)
class RepoMemorySnapshot:
    accepted_change_summaries: tuple[dict[str, object], ...] = ()
    unresolved_blockers: tuple[dict[str, object], ...] = ()
    deferred_issue_summaries: tuple[dict[str, object], ...] = ()
    repo_memory_entries: tuple[dict[str, object], ...] = ()
    carry_forward_summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted_change_summaries": [dict(item) for item in self.accepted_change_summaries],
            "unresolved_blockers": [dict(item) for item in self.unresolved_blockers],
            "deferred_issue_summaries": [dict(item) for item in self.deferred_issue_summaries],
            "repo_memory_entries": [dict(item) for item in self.repo_memory_entries],
            "carry_forward_summary": self.carry_forward_summary,
        }



@dataclass(frozen=True)
class BacklogSelectionTruth:
    selected_task_path: str = ""
    selected_reason: str = ""
    reordered: bool = False
    ready_task_paths: tuple[str, ...] = ()
    blocked_task_paths: tuple[str, ...] = ()
    deferred_task_paths: tuple[str, ...] = ()
    skipped_task_paths: tuple[str, ...] = ()
    rerun_required_task_paths: tuple[str, ...] = ()
    ranked_candidate_paths: tuple[str, ...] = ()
    ranked_candidates: tuple[dict[str, object], ...] = ()
    blocking_reasons: tuple[tuple[str, str], ...] = ()
    skip_reasons: tuple[tuple[str, str], ...] = ()
    priority_by_task: tuple[tuple[str, int], ...] = ()
    carry_forward_summary_used: str = ""
    carry_forward_related_task_paths: tuple[str, ...] = ()
    carry_forward_blocked_task_paths: tuple[str, ...] = ()
    hosted_authority_ready: bool = False
    selection_policy: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_task_path": self.selected_task_path,
            "selected_reason": self.selected_reason,
            "reordered": self.reordered,
            "ready_task_paths": list(self.ready_task_paths),
            "blocked_task_paths": list(self.blocked_task_paths),
            "deferred_task_paths": list(self.deferred_task_paths),
            "skipped_task_paths": list(self.skipped_task_paths),
            "rerun_required_task_paths": list(self.rerun_required_task_paths),
            "ranked_candidate_paths": list(self.ranked_candidate_paths),
            "ranked_candidates": [dict(item) for item in self.ranked_candidates],
            "blocking_reasons": {task_path: reason for task_path, reason in self.blocking_reasons},
            "skip_reasons": {task_path: reason for task_path, reason in self.skip_reasons},
            "priority_by_task": {task_path: priority for task_path, priority in self.priority_by_task},
            "carry_forward_summary_used": self.carry_forward_summary_used,
            "carry_forward_related_task_paths": list(self.carry_forward_related_task_paths),
            "carry_forward_blocked_task_paths": list(self.carry_forward_blocked_task_paths),
            "hosted_authority_ready": self.hosted_authority_ready,
            "selection_policy": dict(self.selection_policy or {}),
        }


def manifest_planner_snapshot() -> dict[str, object]:
    return asdict(ManifestPlannerSnapshot())





def _normalized_path_value(raw: object) -> str:
    return str(raw or "").strip().replace("\\", "/")


def _normalized_priority_value(raw: object) -> int:
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _normalized_authority_prerequisite(raw: object) -> str:
    value = str(raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    if value in {"", "none", "local", "local_only"}:
        return "none"
    if value in {"hosted", "required_ci", "local_plus_required_ci", "hosted_required"}:
        return "hosted"
    return value or "none"


def normalize_manifest_entry_schema(entry: Any, *, index: int = 0) -> dict[str, object]:
    if isinstance(entry, str):
        task_path = _normalized_path_value(entry)
        if not task_path:
            raise ValueError(f"Manifest entry at index {index} is empty.")
        task_id = Path(task_path).stem or f"task_{index+1}"
        return {
            "task_id": task_id,
            "path": task_path,
            "task_path": task_path,
            "label": "",
            "note": "",
            "stop_policy": "",
            "depends_on": [],
            "blocks": [],
            "deferrable": False,
            "skipped_by_policy": False,
            "rerun_required": False,
            "priority": 0,
            "authority_prerequisite": "none",
            "required_paths": [],
            "decomposition_safe": False,
            "decomposition_max_unit_size": 3,
        }
    if not isinstance(entry, Mapping):
        raise ValueError(f"Manifest entry at index {index} must be a string or mapping.")
    task_path = _normalized_path_value(entry.get("path") or entry.get("task_path"))
    if not task_path:
        raise ValueError(f"Manifest entry at index {index} is missing `path` or `task_path`.")
    task_id = str(entry.get("task_id") or Path(task_path).stem or f"task_{index+1}").strip()
    def _path_list(v: object) -> list[str]:
        if v in (None, ""):
            return []
        if not isinstance(v, (list, tuple)):
            raise ValueError(f"Manifest entry at index {index} dependency field must be a list.")
        return [_normalized_path_value(x) for x in v if _normalized_path_value(x)]
    return {
        "task_id": task_id,
        "path": task_path,
        "task_path": task_path,
        "label": str(entry.get("label") or "").strip(),
        "note": str(entry.get("note") or "").strip(),
        "stop_policy": str(entry.get("stop_policy") or "").strip(),
        "depends_on": _path_list(entry.get("depends_on")),
        "blocks": _path_list(entry.get("blocks")),
        "deferrable": bool(entry.get("deferrable", entry.get("optional", False))),
        "skipped_by_policy": bool(entry.get("skipped_by_policy", entry.get("skip_by_policy", False))),
        "rerun_required": bool(entry.get("rerun_required", False)),
        "priority": _normalized_priority_value(entry.get("priority", 0)),
        "authority_prerequisite": _normalized_authority_prerequisite(entry.get("authority_prerequisite", "none")),
        "required_paths": _path_list(entry.get("required_paths")),
        "decomposition_safe": bool(entry.get("decomposition_safe", False)),
        "decomposition_max_unit_size": max(1, _normalized_priority_value(entry.get("decomposition_max_unit_size", 3)) or 3),
    }


def normalize_manifest_entries_schema(task_manifest: Mapping[str, Any] | Sequence[Any]) -> list[dict[str, object]]:
    raw_tasks = task_manifest.get("tasks", []) if isinstance(task_manifest, Mapping) else task_manifest
    return [normalize_manifest_entry_schema(raw, index=i) for i, raw in enumerate(raw_tasks)]


def _reverse_block_edges(queue: Sequence[Any]) -> dict[str, tuple[str, ...]]:
    blocked_by: dict[str, list[str]] = {}
    for item in queue:
        for blocked in item.blocks:
            blocked_by.setdefault(blocked, []).append(item.task_path)
    return {task_path: tuple(sorted(paths)) for task_path, paths in blocked_by.items()}


def _reason_for_task(
    item: Any,
    *,
    completed_paths: set[str],
    blocking_edges: Mapping[str, Sequence[str]],
    status_by_path: Mapping[str, str],
) -> str:
    missing = [dep for dep in item.depends_on if dep not in completed_paths]
    if missing:
        return "missing_prerequisites:" + ",".join(sorted(missing))

    active_blockers = [
        blocker
        for blocker in blocking_edges.get(item.task_path, ())
        if status_by_path.get(blocker, "queued") != "completed"
    ]
    if active_blockers:
        return "blocked_by:" + ",".join(sorted(active_blockers))
    return ""



def plan_manifest_progress(queue: Sequence[Any]) -> dict[str, object]:
    completed_paths = {item.task_path for item in queue if item.status == "completed"}
    blocking_edges = _reverse_block_edges(queue)
    status_by_path = {item.task_path: item.status for item in queue}

    ready: list[str] = []
    blocked: list[str] = []
    deferred: list[str] = []
    skipped: list[str] = []
    rerun_required: list[str] = []
    blocking_reasons: dict[str, str] = {}

    for item in queue:
        if item.status == "completed":
            continue
        if item.skipped_by_policy:
            skipped.append(item.task_path)
            continue
        reason = _reason_for_task(
            item,
            completed_paths=completed_paths,
            blocking_edges=blocking_edges,
            status_by_path=status_by_path,
        )
        if reason:
            blocked.append(item.task_path)
            blocking_reasons[item.task_path] = reason
            if item.deferrable:
                deferred.append(item.task_path)
            continue
        ready.append(item.task_path)
        if item.rerun_required and any(dep in completed_paths for dep in item.depends_on):
            rerun_required.append(item.task_path)

    selected = ""
    reordered = False
    first_unresolved = next(
        (
            item.task_path
            for item in queue
            if item.status != "completed" and not item.skipped_by_policy
        ),
        "",
    )
    for item in queue:
        if item.status == "completed" or item.skipped_by_policy:
            continue
        if item.task_path in ready:
            selected = item.task_path
            reordered = bool(first_unresolved and first_unresolved != selected)
            break
        if item.task_path in blocked and not item.deferrable:
            break

    truth = ManifestPlannerTruth(
        selected_task_path=selected,
        reordered=reordered,
        ready_task_paths=tuple(ready),
        blocked_task_paths=tuple(blocked),
        deferred_task_paths=tuple(deferred),
        skipped_task_paths=tuple(skipped),
        rerun_required_task_paths=tuple(rerun_required),
        blocking_reasons=tuple(sorted(blocking_reasons.items())),
    )
    return truth.to_dict()



def build_manifest_entry_decomposition_truth(entry: Mapping[str, object] | Any) -> dict[str, object]:
    required_paths = tuple(_dedupe_paths(getattr(entry, "required_paths", None) if not isinstance(entry, Mapping) else entry.get("required_paths") or ()))
    decomposition_safe = bool(getattr(entry, "decomposition_safe", None) if not isinstance(entry, Mapping) else entry.get("decomposition_safe", False))
    max_paths_per_unit = max(1, int(getattr(entry, "decomposition_max_unit_size", None) if not isinstance(entry, Mapping) else entry.get("decomposition_max_unit_size", 3) or 3))

    base_truth = dict(build_bounded_decomposition_truth(required_paths, max_paths_per_unit=max_paths_per_unit))
    if base_truth["decomposition_status"] == "required" and not decomposition_safe:
        base_truth["decomposition_status"] = "manual_only"
        base_truth["bounded_decomposition_required"] = False
        base_truth["decomposition_summary"] = "Large task shape detected, but bounded decomposition is not marked safe for autonomous planning."
    return base_truth


def build_dependency_graph_truth(queue: Sequence[Any]) -> dict[str, object]:
    completed_paths = {item.task_path for item in queue if getattr(item, "status", "queued") == "completed"}
    dependency_nodes = tuple(item.task_path for item in queue)
    dependency_edges: list[tuple[str, str]] = []
    blocking_edges: list[tuple[str, str]] = []
    unresolved: list[tuple[str, tuple[str, ...]]] = []
    blocked: list[str] = []
    decomp_required: list[str] = []
    decomp_manual: list[str] = []

    for item in queue:
        for dep in getattr(item, "depends_on", ()):
            dependency_edges.append((str(dep), item.task_path))
        for blocked_task in getattr(item, "blocks", ()):
            blocking_edges.append((item.task_path, str(blocked_task)))
        missing = tuple(sorted(dep for dep in getattr(item, "depends_on", ()) if dep not in completed_paths))
        if missing:
            unresolved.append((item.task_path, missing))
            blocked.append(item.task_path)
        decomposition_status = str(getattr(item, "decomposition_status", "not_required") or "not_required")
        if decomposition_status == "required":
            decomp_required.append(item.task_path)
        elif decomposition_status == "manual_only":
            decomp_manual.append(item.task_path)
            if item.task_path not in blocked:
                blocked.append(item.task_path)

    truth = DependencyGraphTruth(
        dependency_nodes=dependency_nodes,
        dependency_edges=tuple(dependency_edges),
        blocking_edges=tuple(blocking_edges),
        unresolved_dependencies=tuple(unresolved),
        blocked_by_dependencies=tuple(blocked),
        decomposition_required_task_paths=tuple(decomp_required),
        decomposition_manual_only_task_paths=tuple(decomp_manual),
    )
    return truth.to_dict()


def plan_dependency_decomposition(queue: Sequence[Any]) -> dict[str, object]:
    planner_truth = dict(plan_manifest_progress(queue))
    graph_truth = build_dependency_graph_truth(queue)
    decomposition_by_task: dict[str, dict[str, object]] = {}
    for item in queue:
        decomposition_by_task[item.task_path] = {
            "decomposition_status": str(getattr(item, "decomposition_status", "not_required") or "not_required"),
            "bounded_decomposition_required": bool(getattr(item, "bounded_decomposition_required", False)),
            "decomposition_unit_count": int(getattr(item, "decomposition_unit_count", 0) or 0),
            "decomposition_summary": str(getattr(item, "decomposition_summary", "") or ""),
            "decomposition_units": [
                {"label": label, "task_paths": list(paths)}
                for label, paths in getattr(item, "decomposition_units", ())
            ],
        }
    return {
        **planner_truth,
        "dependency_graph": graph_truth,
        "decomposition_by_task": decomposition_by_task,
    }


def _carry_forward_related_and_blocked_paths(repo_memory: Mapping[str, object] | None) -> tuple[set[str], set[str], str]:
    memory = dict(repo_memory or {})
    related = {
        _normalized_path_value(item.get("task_path"))
        for item in list(memory.get("accepted_change_summaries") or [])
        if isinstance(item, Mapping) and _normalized_path_value(item.get("task_path"))
    }
    blocked = set()
    for bucket_name in ("unresolved_blockers", "deferred_issue_summaries"):
        for item in list(memory.get(bucket_name) or []):
            if isinstance(item, Mapping):
                task_path = _normalized_path_value(item.get("task_path"))
                if task_path:
                    blocked.add(task_path)
    summary = str(memory.get("carry_forward_summary") or "").strip()
    return related, blocked, summary


def select_next_backlog_task(
    queue: Sequence[Any],
    *,
    project_contract: Mapping[str, object] | None = None,
    repo_memory: Mapping[str, object] | None = None,
    hosted_authority_ready: bool = False,
) -> dict[str, object]:
    from agents.lib.project_registry import project_backlog_selection_contract

    planner_truth = dict(plan_manifest_progress(queue))
    ready_paths = list(planner_truth["ready_task_paths"])
    blocked_paths = list(planner_truth["blocked_task_paths"])
    deferred_paths = list(planner_truth["deferred_task_paths"])
    skipped_paths = list(planner_truth["skipped_task_paths"])
    rerun_required_paths = list(planner_truth["rerun_required_task_paths"])
    blocking_reasons = dict(planner_truth["blocking_reasons"])
    skip_reasons = {task_path: "skipped_by_policy" for task_path in skipped_paths}
    priority_by_task: dict[str, int] = {}
    carry_forward_related, carry_forward_blocked, carry_forward_summary = _carry_forward_related_and_blocked_paths(repo_memory)
    selection_policy = dict(project_backlog_selection_contract(project_contract))
    ranked_candidates: list[dict[str, object]] = []

    first_unresolved = next((item.task_path for item in queue if item.status != "completed" and not item.skipped_by_policy), "")

    for item in queue:
        if item.status == "completed":
            continue
        priority = int(getattr(item, "priority", 0) or 0)
        priority_by_task[item.task_path] = priority
        if item.skipped_by_policy:
            continue
        if item.task_path in carry_forward_blocked and item.task_path not in blocking_reasons:
            blocking_reasons[item.task_path] = "carry_forward_blocked"
            if item.task_path not in blocked_paths:
                blocked_paths.append(item.task_path)
            if item.deferrable and item.task_path not in deferred_paths:
                deferred_paths.append(item.task_path)
            continue
        decomposition_status = str(getattr(item, "decomposition_status", "not_required") or "not_required")
        if decomposition_status == "manual_only":
            blocking_reasons[item.task_path] = "decomposition_not_safe"
            if item.task_path not in blocked_paths:
                blocked_paths.append(item.task_path)
            if item.deferrable and item.task_path not in deferred_paths:
                deferred_paths.append(item.task_path)
            continue
        authority_prereq = _normalized_authority_prerequisite(getattr(item, "authority_prerequisite", "none"))
        if authority_prereq == "hosted" and not hosted_authority_ready:
            blocking_reasons[item.task_path] = "authority_prerequisite_unsatisfied:hosted"
            if item.task_path not in blocked_paths:
                blocked_paths.append(item.task_path)
            if item.deferrable and item.task_path not in deferred_paths:
                deferred_paths.append(item.task_path)
            continue
        if item.task_path not in ready_paths:
            continue
        carry_forward_related_candidate = bool(item.task_path in carry_forward_related or any(dep in carry_forward_related for dep in item.depends_on))
        rerun_required = bool(item.task_path in rerun_required_paths or getattr(item, "rerun_required", False))
        ranked_candidates.append(
            {
                "task_path": item.task_path,
                "ordinal": int(getattr(item, "ordinal", 0) or 0),
                "priority": priority,
                "rerun_required": rerun_required,
                "carry_forward_related": carry_forward_related_candidate,
                "authority_prerequisite": authority_prereq,
                "_sort_key": (-priority, -int(carry_forward_related_candidate), -int(rerun_required), int(getattr(item, "ordinal", 0) or 0), item.task_path),
            }
        )

    ranked_candidates.sort(key=lambda item: item["_sort_key"])
    cleaned_ranked_candidates = []
    for item in ranked_candidates:
        cleaned = dict(item)
        cleaned.pop("_sort_key", None)
        cleaned_ranked_candidates.append(cleaned)

    selected_task_path = cleaned_ranked_candidates[0]["task_path"] if cleaned_ranked_candidates else ""
    reordered = bool(selected_task_path and first_unresolved and selected_task_path != first_unresolved)
    selected_reason = ""
    if cleaned_ranked_candidates:
        chosen = cleaned_ranked_candidates[0]
        if bool(chosen["carry_forward_related"]) and int(chosen["priority"]) > 0:
            selected_reason = "selected_by_priority_and_carry_forward"
        elif bool(chosen["carry_forward_related"]):
            selected_reason = "selected_by_carry_forward"
        elif int(chosen["priority"]) > 0:
            selected_reason = "selected_by_priority"
        elif bool(chosen["rerun_required"]):
            selected_reason = "selected_by_rerun_requirement"
        elif reordered:
            selected_reason = "selected_by_ready_reordering"
        else:
            selected_reason = "selected_by_manifest_order"

    truth = BacklogSelectionTruth(
        selected_task_path=selected_task_path,
        selected_reason=selected_reason,
        reordered=reordered,
        ready_task_paths=tuple(ready_paths),
        blocked_task_paths=tuple(dict.fromkeys(blocked_paths)),
        deferred_task_paths=tuple(dict.fromkeys(deferred_paths)),
        skipped_task_paths=tuple(skipped_paths),
        rerun_required_task_paths=tuple(rerun_required_paths),
        ranked_candidate_paths=tuple(item["task_path"] for item in cleaned_ranked_candidates),
        ranked_candidates=tuple(dict(item) for item in cleaned_ranked_candidates),
        blocking_reasons=tuple(sorted((str(k), str(v)) for k, v in blocking_reasons.items())),
        skip_reasons=tuple(sorted((str(k), str(v)) for k, v in skip_reasons.items())),
        priority_by_task=tuple(sorted((str(k), int(v)) for k, v in priority_by_task.items())),
        carry_forward_summary_used=carry_forward_summary,
        carry_forward_related_task_paths=tuple(sorted(path for path in {item["task_path"] for item in cleaned_ranked_candidates if bool(item["carry_forward_related"]) })),
        carry_forward_blocked_task_paths=tuple(sorted(carry_forward_blocked)),
        hosted_authority_ready=bool(hosted_authority_ready),
        selection_policy=selection_policy,
    )
    return truth.to_dict()


def choose_next_manifest_task(queue: Sequence[Any]) -> str:
    return str(select_next_backlog_task(queue)["selected_task_path"])



def _dedupe_paths(paths: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in paths:
        path = _normalized_path_value(raw)
        if not path or path in seen:
            continue
        normalized.append(path)
        seen.add(path)
    return normalized


def _decomposition_group_for_path(path: str) -> str:
    if path == "README.md" or path.startswith("docs/"):
        return "docs"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("agents/") or path.startswith("src/"):
        return "code"
    if path.startswith("tasks/"):
        return "tasks"
    return "other"


def build_bounded_decomposition_truth(required_paths: Sequence[object] | None, *, max_paths_per_unit: int = 3) -> dict[str, object]:
    paths = _dedupe_paths(required_paths or ())
    groups: dict[str, list[str]] = {}
    for path in paths:
        groups.setdefault(_decomposition_group_for_path(path), []).append(path)

    ordered_groups = [name for name in ("code", "tests", "docs", "tasks", "other") if groups.get(name)]
    units: list[tuple[str, tuple[str, ...]]] = []
    for name in ordered_groups:
        bucket = groups[name]
        for idx in range(0, len(bucket), max_paths_per_unit):
            chunk = tuple(bucket[idx:idx + max_paths_per_unit])
            suffix = "" if idx == 0 else f"_{idx // max_paths_per_unit + 1}"
            units.append((f"{name}{suffix}", chunk))

    group_count = len(ordered_groups)
    total_paths = len(paths)
    required = total_paths >= 5 or group_count >= 3
    suggested = not required and total_paths >= 3 and group_count >= 2
    status = "required" if required else ("suggested" if suggested else "not_required")
    if status == "required":
        summary = f"Bounded decomposition required: {len(units)} scoped unit(s) across {group_count} surface group(s)."
    elif status == "suggested":
        summary = f"Bounded decomposition suggested: {len(units)} scoped unit(s) across {group_count} surface group(s)."
    else:
        summary = "Bounded decomposition not required for this task shape."

    return TaskDecompositionTruth(
        decomposition_status=status,
        bounded_decomposition_required=(status == "required"),
        decomposition_unit_count=len(units),
        decomposition_summary=summary,
        decomposition_units=tuple(units),
    ).to_dict()


def _bounded_summary_value(raw: object, *, max_chars: int = 140) -> str:
    value = str(raw or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 13].rstrip() + "...[truncated]"


def _bounded_changed_files(raw: object, *, limit: int = 3) -> list[str]:
    if not isinstance(raw, (list, tuple)):
        return []
    out: list[str] = []
    for item in raw:
        path = _normalized_path_value(item)
        if path and path not in out:
            out.append(path)
        if len(out) >= limit:
            break
    return out


def _checkpoint_summary(checkpoint: Any) -> str:
    for envelope_name in ("controller_artifact_envelope", "tester_artifact_envelope", "coder_artifact_envelope"):
        envelope = getattr(checkpoint, envelope_name, {}) or {}
        if isinstance(envelope, Mapping):
            summary = _bounded_summary_value(envelope.get("summary"))
            if summary:
                return summary
    return _bounded_summary_value(getattr(checkpoint, "note", ""))


def _accepted_change_entry(checkpoint: Any) -> dict[str, object]:
    coder = getattr(checkpoint, "coder_artifact_envelope", {}) or {}
    return {
        "task_path": str(getattr(checkpoint, "task_path", "") or ""),
        "summary": _checkpoint_summary(checkpoint),
        "changed_files": _bounded_changed_files(coder.get("changed_files")),
        "event_seq": int(getattr(checkpoint, "event_seq", 0) or 0),
    }


def _unresolved_blocker_entry(checkpoint: Any) -> dict[str, object]:
    return {
        "task_path": str(getattr(checkpoint, "task_path", "") or ""),
        "summary": _checkpoint_summary(checkpoint),
        "terminal_status": str(getattr(checkpoint, "terminal_status", "") or ""),
        "post_task_decision": str(getattr(checkpoint, "post_task_decision", "") or ""),
        "event_seq": int(getattr(checkpoint, "event_seq", 0) or 0),
    }


def build_bounded_repo_memory(
    checkpoints: Sequence[Any],
    *,
    planner_truth: Mapping[str, object] | None = None,
    max_accepts: int = 4,
    max_blockers: int = 4,
    max_deferred: int = 4,
    max_entries: int = 8,
) -> dict[str, object]:
    accepted_by_task: dict[str, dict[str, object]] = {}
    blockers_by_task: dict[str, dict[str, object]] = {}

    for checkpoint in checkpoints:
        task_path = str(getattr(checkpoint, "task_path", "") or "")
        if not task_path:
            continue
        accepted = str(getattr(checkpoint, "acceptance_decision", "") or "") == "accepted" and str(getattr(checkpoint, "terminal_status", "") or "") == "completed"
        if accepted:
            accepted_by_task[task_path] = _accepted_change_entry(checkpoint)
            blockers_by_task.pop(task_path, None)
            continue
        is_blocked = (
            not bool(getattr(checkpoint, "next_task_may_proceed", True))
            or str(getattr(checkpoint, "terminal_status", "") or "") in {"blocked", "failed", "manual_patch"}
            or str(getattr(checkpoint, "post_task_decision", "") or "") in {"stop", "manual_patch"}
        )
        if is_blocked:
            blockers_by_task[task_path] = _unresolved_blocker_entry(checkpoint)

    accepted_changes = sorted(accepted_by_task.values(), key=lambda item: int(item.get("event_seq", 0)))[-max_accepts:]
    unresolved_blockers = sorted(blockers_by_task.values(), key=lambda item: int(item.get("event_seq", 0)))[-max_blockers:]

    deferred_issue_summaries: list[dict[str, object]] = []
    planner_truth = dict(planner_truth or {})
    blocking_reasons = dict(planner_truth.get("blocking_reasons") or {})
    for task_path in list(planner_truth.get("deferred_task_paths") or [])[:max_deferred]:
        task = _normalized_path_value(task_path)
        if not task:
            continue
        deferred_issue_summaries.append(
            {
                "task_path": task,
                "reason": _bounded_summary_value(blocking_reasons.get(task) or "deferred"),
                "summary": f"Deferred issue remains visible for {task}.",
            }
        )

    repo_memory_entries: list[dict[str, object]] = []
    for item in accepted_changes:
        repo_memory_entries.append({
            "memory_kind": "accepted_change",
            "task_path": str(item.get("task_path") or ""),
            "summary": str(item.get("summary") or ""),
        })
    for item in unresolved_blockers:
        repo_memory_entries.append({
            "memory_kind": "unresolved_blocker",
            "task_path": str(item.get("task_path") or ""),
            "summary": str(item.get("summary") or ""),
        })
    for item in deferred_issue_summaries:
        repo_memory_entries.append({
            "memory_kind": "deferred_issue",
            "task_path": str(item.get("task_path") or ""),
            "summary": str(item.get("reason") or item.get("summary") or ""),
        })
    repo_memory_entries = repo_memory_entries[-max_entries:]

    carry_forward_summary = (
        f"Carry forward {len(accepted_changes)} accepted change(s), "
        f"{len(unresolved_blockers)} unresolved blocker(s), and "
        f"{len(deferred_issue_summaries)} deferred issue(s)."
    )

    return RepoMemorySnapshot(
        accepted_change_summaries=tuple(dict(item) for item in accepted_changes),
        unresolved_blockers=tuple(dict(item) for item in unresolved_blockers),
        deferred_issue_summaries=tuple(dict(item) for item in deferred_issue_summaries),
        repo_memory_entries=tuple(dict(item) for item in repo_memory_entries),
        carry_forward_summary=carry_forward_summary,
    ).to_dict()
