from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Optional

from .backlog_state import BacklogStateEngine, BacklogStatus, BacklogTaskState
from .ci_manager import CIClassification, CIManager, CIState, CIStatus
from .failures import FailureClassifier
from .pr_manager import PRControllerState, PRManager
from .repair import RepairWorkflow


@dataclass(frozen=True)
class TaskExecutionRequest:
    task_id: str
    lane: str
    prompt: str


@dataclass(frozen=True)
class TaskExecutionOutcome:
    success: bool
    runner_output: str
    failure_text: str
    changed_files: list[str] = field(default_factory=list)


@dataclass
class OrchestratorRuntimeState:
    backlog_state: BacklogStateEngine = field(default_factory=BacklogStateEngine)
    active_task_id: Optional[str] = None
    last_selected_task_id: Optional[str] = None
    remediation_context: Dict[str, str] = field(default_factory=dict)
    autonomy_context: Dict[str, str] = field(default_factory=dict)

    def register_task(self, task_id: str, *, status: BacklogStatus = BacklogStatus.READY) -> None:
        existing = self.backlog_state.get(task_id)
        metadata = dict(existing.metadata) if existing else {}
        self.backlog_state.upsert(
            BacklogTaskState(task_id=task_id, status=status, metadata=metadata)
        )

    def set_task_status(
        self,
        task_id: str,
        status: BacklogStatus,
        *,
        reason: Optional[str] = None,
        approval_ref: Optional[str] = None,
        manual_patch_note: Optional[str] = None,
    ) -> None:
        existing = self.backlog_state.get(task_id)
        metadata = dict(existing.metadata) if existing else {}
        self.backlog_state.upsert(
            BacklogTaskState(
                task_id=task_id,
                status=status,
                blocker_reason=reason if status == BacklogStatus.BLOCKED else None,
                waiting_approval_for=approval_ref if status == BacklogStatus.WAITING_APPROVAL else None,
                manual_patch_note=manual_patch_note if status == BacklogStatus.MANUAL_PATCH else None,
                deferred_reason=reason if status == BacklogStatus.DEFERRED else None,
                metadata=metadata,
            )
        )

    def pick_next_ready_task(self, ordered_task_ids: Iterable[str]) -> Optional[str]:
        task = self.backlog_state.next_ready_task(ordered_task_ids)
        if task is None:
            self.active_task_id = None
            return None
        self.active_task_id = task.task_id
        self.last_selected_task_id = task.task_id
        return task.task_id

    def remember_remediation_context(self, **context: str) -> None:
        self.remediation_context.update(context)

    def remember_autonomy_context(self, **context: str) -> None:
        self.autonomy_context.update(context)

    def to_dict(self) -> Dict[str, object]:
        return {
            "active_task_id": self.active_task_id,
            "last_selected_task_id": self.last_selected_task_id,
            "remediation_context": dict(self.remediation_context),
            "autonomy_context": dict(self.autonomy_context),
            "backlog_state": self.backlog_state.as_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "OrchestratorRuntimeState":
        backlog_raw = payload.get("backlog_state", {})
        backlog_state = (
            BacklogStateEngine.from_dict(backlog_raw)
            if isinstance(backlog_raw, dict)
            else BacklogStateEngine()
        )
        remediation = payload.get("remediation_context", {})
        autonomy = payload.get("autonomy_context", {})
        return cls(
            backlog_state=backlog_state,
            active_task_id=payload.get("active_task_id")
            if isinstance(payload.get("active_task_id"), str) or payload.get("active_task_id") is None
            else None,
            last_selected_task_id=payload.get("last_selected_task_id")
            if isinstance(payload.get("last_selected_task_id"), str)
            or payload.get("last_selected_task_id") is None
            else None,
            remediation_context=dict(remediation) if isinstance(remediation, dict) else {},
            autonomy_context=dict(autonomy) if isinstance(autonomy, dict) else {},
        )


@dataclass
class OrchestratorAutonomyLoop:
    runtime_state: OrchestratorRuntimeState = field(default_factory=OrchestratorRuntimeState)
    failure_classifier: FailureClassifier = field(default_factory=FailureClassifier)
    ci_manager: CIManager = field(default_factory=CIManager)
    pr_manager: PRManager = field(default_factory=PRManager)

    def choose_task_family_lane(self, task_id: str) -> str:
        lowered = task_id.lower()
        if "doc" in lowered or lowered.endswith(".md"):
            return "docs"
        if "test" in lowered:
            return "tests"
        return "implementation"

    def compile_request(self, task_id: str, lane: str) -> TaskExecutionRequest:
        return TaskExecutionRequest(
            task_id=task_id,
            lane=lane,
            prompt=f"Execute task '{task_id}' in lane '{lane}' with deterministic constraints.",
        )

    def run_iteration(
        self,
        ordered_task_ids: Iterable[str],
        *,
        execute_task: Callable[[TaskExecutionRequest], TaskExecutionOutcome],
        run_localized_repair: Callable[[str, str], bool],
        ci_provider: Callable[[str], CIStatus],
    ) -> dict[str, object]:
        task_id = self.runtime_state.pick_next_ready_task(ordered_task_ids)
        if task_id is None:
            return {"status": "idle", "task_id": None}

        lane = self.choose_task_family_lane(task_id)
        request = self.compile_request(task_id, lane)
        self.runtime_state.remember_autonomy_context(selected_lane=lane, compiled_prompt=request.prompt)

        outcome = execute_task(request)
        if outcome.success:
            return self._finalize_success(task_id, ci_provider)

        classification = self.failure_classifier.classify(
            outcome.runner_output,
            outcome.failure_text,
            outcome.changed_files,
        )
        category = str(classification.get("category", "unknown"))
        recommended = str(classification.get("recommended_action", "require_human_review"))

        self.runtime_state.remember_remediation_context(
            task_id=task_id,
            failure_category=category,
            recommended_action=recommended,
        )

        repair_plan = RepairWorkflow(category, outcome.changed_files).determine_repair_action()
        should_repair = (
            repair_plan.get("action") in {"clean_repo", "patch_ci", "patch_runner"}
            and not bool(repair_plan.get("requires_approval", True))
        )

        if should_repair:
            repaired = run_localized_repair(task_id, str(repair_plan.get("action", "")))
            if repaired:
                retried = execute_task(request)
                if retried.success:
                    self.runtime_state.remember_remediation_context(repair="applied", repair_action=str(repair_plan.get("action", "")))
                    return self._finalize_success(task_id, ci_provider)

        self.runtime_state.set_task_status(
            task_id,
            BacklogStatus.BLOCKED,
            reason=f"{category}:{repair_plan.get('action', 'require_human_review')}",
        )
        return {"status": "blocked", "task_id": task_id, "category": category}

    def _finalize_success(
        self,
        task_id: str,
        ci_provider: Callable[[str], CIStatus],
    ) -> dict[str, object]:
        pr_decision = self.pr_manager.create_or_open_pr(
            number=1,
            title=f"Task {task_id}",
            branch=f"feature/{task_id}",
        )
        ci_status = ci_provider(task_id)
        ci_decision = self.ci_manager.update_status(ci_status)

        if ci_decision.classification != CIClassification.SAFE_TO_MERGE:
            self.runtime_state.set_task_status(
                task_id,
                BacklogStatus.BLOCKED,
                reason=ci_decision.reason,
            )
            return {
                "status": "blocked",
                "task_id": task_id,
                "ci_classification": ci_decision.classification.value,
            }

        merged = self.pr_manager.mark_ready_to_merge()
        if merged.state != PRControllerState.READY_TO_MERGE:
            self.runtime_state.set_task_status(task_id, BacklogStatus.BLOCKED, reason="pr_not_ready")
            return {"status": "blocked", "task_id": task_id}

        self.pr_manager.mark_merged()
        self.pr_manager.mark_resynced()
        self.pr_manager.unlock_next_task()
        self.runtime_state.set_task_status(task_id, BacklogStatus.COMPLETED)

        return {
            "status": "completed",
            "task_id": task_id,
            "pr_state": pr_decision.state.value,
            "ci_state": ci_status.state.value if ci_status.state in {CIState.PASSED, CIState.FAILED, CIState.RUNNING, CIState.NOT_STARTED} else "unknown",
        }
