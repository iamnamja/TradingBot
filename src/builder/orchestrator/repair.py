from typing import Dict, Any

class RepairWorkflow:
    APPROVAL_REQUIRED_PATTERNS = [
        "task_runner_changes",
        "workflow_ci_changes",
        "dependency_management_changes",
        "secrets_auth_changes",
        "live_trading_safety_changes"
    ]

    def __init__(self, failure_classification: str, changed_files: list):
        self.failure_classification = failure_classification
        self.changed_files = changed_files

    def determine_repair_action(self) -> Dict[str, Any]:
        action, requires_approval, reason = self._classify_failure()
        return {
            "action": action,
            "requires_approval": requires_approval,
            "reason": reason
        }

    def _classify_failure(self) -> tuple:
        if "runner_weakness" in self.failure_classification:
            return "patch_runner", self._requires_approval("task_runner_changes"), "Runner weakness detected."
        elif "ci_dependency_issue" in self.failure_classification:
            return "patch_ci", self._requires_approval("workflow_ci_changes"), "CI dependency issue detected."
        elif "repo_hygiene_issue" in self.failure_classification:
            return "clean_repo", False, "Repository hygiene issue detected."
        elif "task_ambiguity" in self.failure_classification:
            return "require_human_review", True, "Task ambiguity requires human review."
        else:
            return "require_human_review", True, "Unknown failure requires human review."

    def _requires_approval(self, change_type: str) -> bool:
        return change_type in self.APPROVAL_REQUIRED_PATTERNS
