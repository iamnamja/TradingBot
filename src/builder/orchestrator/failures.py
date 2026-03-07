from typing import List, Dict, Any

class FailureClassifier:
    def __init__(self):
        self.categories = {
            "implementation_bug": "Issues related to bugs in the implementation.",
            "task_ambiguity": "Ambiguities in task requirements.",
            "runner_weakness": "Weaknesses in the task runner.",
            "ci_dependency_issue": "Issues with CI dependencies.",
            "repo_hygiene_issue": "Problems related to repository hygiene.",
            "unknown": "Unclassified issues."
        }

    def classify(self, runner_output: str, failure_text: str, changed_files: List[str]) -> Dict[str, Any]:
        if "missing required deliverables" in failure_text:
            return self._create_response("implementation_bug", "High", "patch_task")
        elif "invented import/module path" in failure_text:
            return self._create_response("implementation_bug", "High", "patch_task")
        elif "CI missing dependency" in runner_output:
            return self._create_response("ci_dependency_issue", "Medium", "patch_ci")
        elif "runtime artifact committed" in runner_output:
            return self._create_response("repo_hygiene_issue", "Medium", "clean_repo")
        elif "semantic assertion mismatch" in failure_text:
            return self._create_response("implementation_bug", "High", "require_human_review")
        else:
            return self._create_response("unknown", "Low", "require_human_review")

    def _create_response(self, category: str, confidence: str, action: str) -> Dict[str, Any]:
        return {
            "category": category,
            "confidence": confidence,
            "recommended_action": action
        }
