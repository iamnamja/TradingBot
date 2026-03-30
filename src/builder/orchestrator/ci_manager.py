from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CIState(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


class CIClassification(str, Enum):
    WAIT = "wait"
    SAFE_TO_MERGE = "safe_to_merge"
    REMEDIATE = "remediate"


@dataclass(frozen=True)
class CIStatus:
    state: CIState
    provider: str = "local"
    details: str = ""


@dataclass(frozen=True)
class CIDecision:
    classification: CIClassification
    reason: str
    route_to_remediation: bool


class CIManager:
    def __init__(self) -> None:
        self._last_status = CIStatus(state=CIState.NOT_STARTED)

    @property
    def last_status(self) -> CIStatus:
        return self._last_status

    def update_status(self, status: CIStatus) -> CIDecision:
        self._last_status = status
        if status.state in {CIState.NOT_STARTED, CIState.RUNNING}:
            return CIDecision(
                classification=CIClassification.WAIT,
                reason="CI is still in progress",
                route_to_remediation=False,
            )
        if status.state == CIState.PASSED:
            return CIDecision(
                classification=CIClassification.SAFE_TO_MERGE,
                reason="All CI checks passed",
                route_to_remediation=False,
            )
        return CIDecision(
            classification=CIClassification.REMEDIATE,
            reason=status.details or "CI checks failed",
            route_to_remediation=True,
        )
