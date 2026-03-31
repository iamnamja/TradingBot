from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from agents.lib.task_queue import TaskQueueItem, QueueStatus, validate_queue_status_transition

BatchStatus = Literal["active", "completed", "blocked", "failed", "manual_patch"]


class BatchStateError(ValueError):
    """Raised when batch state persistence or resume validation fails."""


@dataclass(frozen=True)
class BatchTaskState:
    task_path: str
    ordinal: int
    status: QueueStatus
    status_note: str
    attempts: int
    updated_seq: int


@dataclass(frozen=True)
class BatchState:
    manifest_source: str
    manifest_fingerprint: str
    queue: tuple[BatchTaskState, ...]
    current_index: int
    state_version: int
    event_seq: int
    created_ts: int
    updated_ts: int
    batch_status: BatchStatus

    def to_dict(self) -> dict[str, object]:
        return {
            "state_version": self.state_version,
            "manifest": {
                "source": self.manifest_source,
                "fingerprint": self.manifest_fingerprint,
            },
            "queue": [
                {
                    "task_path": item.task_path,
                    "ordinal": item.ordinal,
                    "status": item.status,
                    "status_note": item.status_note,
                    "attempts": item.attempts,
                    "updated_seq": item.updated_seq,
                }
                for item in self.queue
            ],
            "current_index": self.current_index,
            "event_seq": self.event_seq,
            "created_ts": self.created_ts,
            "updated_ts": self.updated_ts,
            "batch_status": self.batch_status,
        }


def manifest_fingerprint(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _derive_batch_status(queue: tuple[BatchTaskState, ...]) -> BatchStatus:
    statuses = [item.status for item in queue]
    if any(status == "running" for status in statuses):
        return "active"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "manual_patch" for status in statuses):
        return "manual_patch"
    if any(status == "failed" for status in statuses):
        return "failed"
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    return "active"


def initialize_batch_state(
    *,
    manifest: dict[str, Any],
    queue: list[TaskQueueItem],
    manifest_source: str,
    created_ts: int = 0,
) -> BatchState:
    queue_state = tuple(
        BatchTaskState(
            task_path=item.task_path,
            ordinal=item.ordinal,
            status="queued",
            status_note="",
            attempts=0,
            updated_seq=0,
        )
        for item in queue
    )
    return BatchState(
        manifest_source=manifest_source,
        manifest_fingerprint=manifest_fingerprint(manifest),
        queue=queue_state,
        current_index=0,
        state_version=1,
        event_seq=0,
        created_ts=created_ts,
        updated_ts=created_ts,
        batch_status="active",
    )


def advance_task_status(
    state: BatchState,
    *,
    task_index: int,
    to_status: QueueStatus,
    status_note: str = "",
    event_ts: int = 0,
) -> BatchState:
    if task_index < 0 or task_index >= len(state.queue):
        raise BatchStateError(f"task_index {task_index} is out of range for queue size {len(state.queue)}.")

    current = state.queue[task_index]
    validate_queue_status_transition(current.status, to_status)

    next_event_seq = state.event_seq + 1
    attempts = current.attempts + (1 if to_status == "running" else 0)
    updated_item = BatchTaskState(
        task_path=current.task_path,
        ordinal=current.ordinal,
        status=to_status,
        status_note=status_note,
        attempts=attempts,
        updated_seq=next_event_seq,
    )

    new_queue = list(state.queue)
    new_queue[task_index] = updated_item

    next_index = state.current_index
    if to_status in {"completed", "failed", "manual_patch", "blocked"} and task_index >= next_index:
        next_index = task_index + 1

    queue_tuple = tuple(new_queue)
    return BatchState(
        manifest_source=state.manifest_source,
        manifest_fingerprint=state.manifest_fingerprint,
        queue=queue_tuple,
        current_index=next_index,
        state_version=state.state_version,
        event_seq=next_event_seq,
        created_ts=state.created_ts,
        updated_ts=event_ts,
        batch_status=_derive_batch_status(queue_tuple),
    )


def write_batch_state(path: str | Path, state: BatchState) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def load_batch_state(path: str | Path) -> BatchState:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    queue = tuple(
        BatchTaskState(
            task_path=str(item["task_path"]),
            ordinal=int(item["ordinal"]),
            status=str(item["status"]),
            status_note=str(item.get("status_note", "")),
            attempts=int(item.get("attempts", 0)),
            updated_seq=int(item.get("updated_seq", 0)),
        )
        for item in data.get("queue", [])
    )
    manifest = data.get("manifest", {})
    return BatchState(
        manifest_source=str(manifest.get("source", "")),
        manifest_fingerprint=str(manifest.get("fingerprint", "")),
        queue=queue,
        current_index=int(data.get("current_index", 0)),
        state_version=int(data.get("state_version", 1)),
        event_seq=int(data.get("event_seq", 0)),
        created_ts=int(data.get("created_ts", 0)),
        updated_ts=int(data.get("updated_ts", 0)),
        batch_status=str(data.get("batch_status", _derive_batch_status(queue))),
    )


def resume_batch_state(
    *,
    state_path: str | Path,
    manifest: dict[str, Any],
    manifest_source: str,
    allow_manifest_source_mismatch: bool = False,
) -> BatchState:
    state = load_batch_state(state_path)
    expected_fingerprint = manifest_fingerprint(manifest)

    if state.manifest_fingerprint != expected_fingerprint:
        raise BatchStateError(
            "Cannot resume batch: manifest fingerprint mismatch between state and provided manifest."
        )

    if not allow_manifest_source_mismatch and state.manifest_source != manifest_source:
        raise BatchStateError(
            f"Cannot resume batch: manifest source mismatch (state={state.manifest_source}, provided={manifest_source})."
        )

    return state
