from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PRControllerState(str, Enum):
    IDLE = "idle"
    OPEN = "open"
    READY_TO_MERGE = "ready_to_merge"
    MERGED = "merged"
    RESYNCED = "resynced"
    NEXT_TASK_UNLOCKED = "next_task_unlocked"


@dataclass(frozen=True)
class PRRecord:
    number: int
    title: str
    branch: str
    base: str
    url: str


@dataclass(frozen=True)
class PRControllerDecision:
    state: PRControllerState
    pr: PRRecord | None
    next_action: str


class PRManager:
    def __init__(self) -> None:
        self._pr: PRRecord | None = None
        self._state = PRControllerState.IDLE

    @property
    def state(self) -> PRControllerState:
        return self._state

    @property
    def current_pr(self) -> PRRecord | None:
        return self._pr

    def create_or_open_pr(
        self,
        *,
        number: int,
        title: str,
        branch: str,
        base: str = "main",
        url: str = "",
    ) -> PRControllerDecision:
        if self._pr is None:
            self._pr = PRRecord(
                number=number,
                title=title,
                branch=branch,
                base=base,
                url=url or f"https://example.invalid/pr/{number}",
            )
        self._state = PRControllerState.OPEN
        return PRControllerDecision(
            state=self._state,
            pr=self._pr,
            next_action="poll_ci",
        )

    def mark_ready_to_merge(self) -> PRControllerDecision:
        if self._pr is None:
            return PRControllerDecision(
                state=self._state,
                pr=None,
                next_action="create_or_open_pr",
            )
        self._state = PRControllerState.READY_TO_MERGE
        return PRControllerDecision(
            state=self._state,
            pr=self._pr,
            next_action="merge_pr",
        )

    def mark_merged(self) -> PRControllerDecision:
        if self._pr is None:
            return PRControllerDecision(
                state=self._state,
                pr=None,
                next_action="create_or_open_pr",
            )
        self._state = PRControllerState.MERGED
        return PRControllerDecision(
            state=self._state,
            pr=self._pr,
            next_action="resync_main",
        )

    def mark_resynced(self) -> PRControllerDecision:
        if self._pr is None:
            return PRControllerDecision(
                state=self._state,
                pr=None,
                next_action="create_or_open_pr",
            )
        self._state = PRControllerState.RESYNCED
        return PRControllerDecision(
            state=self._state,
            pr=self._pr,
            next_action="unlock_next_task",
        )

    def unlock_next_task(self) -> PRControllerDecision:
        self._state = PRControllerState.NEXT_TASK_UNLOCKED
        return PRControllerDecision(
            state=self._state,
            pr=self._pr,
            next_action="run_next_task",
        )
