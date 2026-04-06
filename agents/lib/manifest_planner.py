from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

@dataclass(frozen=True)
class ManifestPlannerSnapshot:
    dependency_surface_enabled: bool = True
    supports_depends_on: bool = True
    supports_blocks: bool = True
    supports_deferrable: bool = True
    supports_skipped_by_policy: bool = True
    supports_rerun_required: bool = True
    conservative_reordering_only: bool = True


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
