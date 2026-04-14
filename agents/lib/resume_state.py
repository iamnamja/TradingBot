from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CheckpointStage(str, Enum):
    STARTED = "STARTED"
    ADMISSION_OK = "ADMISSION_OK"
    WORKSPACE_PREPARED = "WORKSPACE_PREPARED"
    PRECHECKS_PASSED = "PRECHECKS_PASSED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    PARTIAL_PROGRESS = "PARTIAL_PROGRESS"
    EXECUTION_COMPLETE = "EXECUTION_COMPLETE"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    MERGE_SAFE = "MERGE_SAFE"


@dataclass
class ResumeCheckpoint:
    stage: CheckpointStage
    surface: str
    ts: float
    safe: bool = True
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "surface": self.surface,
            "ts": self.ts,
            "safe": self.safe,
            "details": self.details or {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResumeCheckpoint":
        stage_val = data.get("stage")
        if not stage_val:
            raise ValueError("Missing checkpoint stage")
        return cls(
            stage=CheckpointStage(stage_val),
            surface=str(data.get("surface", "")),
            ts=float(data.get("ts", 0.0)),
            safe=bool(data.get("safe", False)),
            details=data.get("details") or {},
        )


@dataclass
class AttemptStateRecord:
    attempt_id: str
    created_at: float
    updated_at: float
    last_checkpoint: Optional[ResumeCheckpoint] = None
    failure_count: int = 0
    manual_intervention: bool = False
    checkpoint_history: List[ResumeCheckpoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_checkpoint": self.last_checkpoint.to_dict() if self.last_checkpoint else None,
            "failure_count": self.failure_count,
            "manual_intervention": self.manual_intervention,
            "checkpoint_history": [c.to_dict() for c in self.checkpoint_history],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttemptStateRecord":
        last = data.get("last_checkpoint")
        last_checkpoint = ResumeCheckpoint.from_dict(last) if last else None
        history = data.get("checkpoint_history") or []
        checkpoint_history = [ResumeCheckpoint.from_dict(x) for x in history]

        return cls(
            attempt_id=str(data.get("attempt_id", "")),
            created_at=float(data.get("created_at", 0.0)),
            updated_at=float(data.get("updated_at", 0.0)),
            last_checkpoint=last_checkpoint,
            failure_count=int(data.get("failure_count", 0)),
            manual_intervention=bool(data.get("manual_intervention", False)),
            checkpoint_history=checkpoint_history,
        )


__all__ = [
    "CheckpointStage",
    "ResumeCheckpoint",
    "AttemptStateRecord",
]
