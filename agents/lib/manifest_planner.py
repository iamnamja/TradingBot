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


def manifest_planner_snapshot() -> dict[str, object]:
    return asdict(ManifestPlannerSnapshot())





def _normalized_path_value(raw: object) -> str:
    return str(raw or "").strip().replace("\\", "/")


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



def choose_next_manifest_task(queue: Sequence[Any]) -> str:
    return str(plan_manifest_progress(queue)["selected_task_path"])



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
