from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

QueueStatus = Literal["queued", "running", "completed", "blocked", "failed", "manual_patch"]

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


def _normalized_task_path(raw_path: str) -> str:
    return raw_path.strip().replace("\\", "/")


def _coerce_manifest_task_entry(entry: Any, index: int) -> dict[str, str]:
    if isinstance(entry, str):
        path = _normalized_task_path(entry)
        if not path:
            raise TaskQueueManifestError(f"Task entry at index {index} is empty.")
        return {"path": path, "label": "", "note": ""}

    if isinstance(entry, dict):
        path = _normalized_task_path(str(entry.get("path", "")))
        if not path:
            raise TaskQueueManifestError(f"Task entry at index {index} is missing `path`.")
        label = str(entry.get("label", "")).strip()
        note = str(entry.get("note", "")).strip()
        return {"path": path, "label": label, "note": note}

    raise TaskQueueManifestError(
        f"Task entry at index {index} must be a string path or object with `path`."
    )


def validate_queue_status_transition(from_status: QueueStatus, to_status: QueueStatus) -> None:
    allowed = ALLOWED_STATUS_TRANSITIONS.get(from_status, ())
    if to_status not in allowed:
        raise TaskQueueTransitionError(
            f"Invalid queue status transition: {from_status} -> {to_status}."
        )


def queue_signature(queue: list[TaskQueueItem]) -> tuple[str, ...]:
    return tuple(item.task_path for item in queue)


def build_task_queue_from_manifest(manifest: dict[str, Any], repo_root: str | Path = ".") -> list[TaskQueueItem]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise TaskQueueManifestError("Manifest must include `tasks` list before queue construction.")

    policy = manifest.get("policy", {})
    if not isinstance(policy, dict):
        policy = {}

    duplicate_policy = str(policy.get("duplicate_policy", "reject")).strip().lower()
    stop_policy = str(policy.get("stop_policy", "")).strip()

    if duplicate_policy not in {"reject", "dedupe_keep_first"}:
        raise TaskQueueManifestError(
            "Manifest policy `duplicate_policy` must be one of: reject, dedupe_keep_first."
        )

    root = Path(repo_root).resolve()
    seen: dict[str, int] = {}
    missing: list[str] = []
    entries: list[dict[str, str]] = []

    for idx, raw_entry in enumerate(tasks):
        entry = _coerce_manifest_task_entry(raw_entry, idx)
        path = entry["path"]

        if path in seen:
            first = seen[path]
            if duplicate_policy == "reject":
                raise TaskQueueManifestError(
                    f"Duplicate task path `{path}` at index {idx} (already seen at index {first})."
                )
            continue

        seen[path] = idx
        if not (root / path).exists():
            missing.append(path)
        entries.append(entry)

    if missing:
        raise TaskQueueManifestError("Missing task file(s): " + ", ".join(missing))

    queue: list[TaskQueueItem] = []
    for ordinal, entry in enumerate(entries, start=1):
        queue.append(
            TaskQueueItem(
                task_path=entry["path"],
                ordinal=ordinal,
                status="queued",
                status_note="",
                label=entry["label"],
                note=entry["note"],
                stop_policy=stop_policy,
            )
        )

    return queue
