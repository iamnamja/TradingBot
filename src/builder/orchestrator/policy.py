from typing import List, Dict

class PolicyEngine:
    def __init__(self, protected_file_patterns: List[str], approval_required_file_patterns: List[str]):
        self.protected_file_patterns = protected_file_patterns
        self.approval_required_file_patterns = approval_required_file_patterns

    def evaluate(self, changed_files: List[str], failure_category: str, requested_action: str) -> Dict[str, str]:
        if self._is_protected_file_change(changed_files):
            return {"decision": "blocked", "reason": "Protected file modification."}
        
        if self._requires_approval(failure_category, requested_action):
            return {"decision": "requires_approval", "reason": "Approval required for this action."}
        
        return {"decision": "allowed", "reason": "Action allowed."}

    def _is_protected_file_change(self, changed_files: List[str]) -> bool:
        return any(file in self.protected_file_patterns for file in changed_files)

    def _requires_approval(self, failure_category: str, requested_action: str) -> bool:
        if failure_category in ["workflow_ci_changes", "dependency_management_changes", "live_trading_safety_changes"]:
            return True
        if requested_action in self.approval_required_file_patterns:
            return True
        return False
