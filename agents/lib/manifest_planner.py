
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from agents.lib.public_compat import coerce_manifest_entry_path


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
    task_path = _normalized_path_value(coerce_manifest_entry_path(entry))
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




def build_dependency_graph(task_manifest: Mapping[str, Any] | Sequence[Any]) -> dict[str, tuple[str, ...]]:
    entries = normalize_manifest_entries_schema(task_manifest)
    return {
        str(entry['task_path']): tuple(str(p) for p in entry.get('depends_on', []))
        for entry in entries
    }

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