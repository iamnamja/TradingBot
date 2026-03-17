from typing import List, Dict, Any

class ReviewChecker:
    def __init__(self, deliverables: List[str], changed_files: List[str]):
        self.deliverables = set(deliverables)
        self.changed_files = changed_files

    def evaluate(self) -> Dict[str, Any]:
        reasons = []
        warnings = []
        
        in_scope_changed = any(file in self.deliverables for file in self.changed_files)
        unexpected_changes = sorted(
            [file for file in self.changed_files if file not in self.deliverables and not self.is_runtime_artifact(file)]
        )
        
        if not in_scope_changed:
            missing_deliverables = sorted(self.deliverables)
            reasons.append(f"Missing deliverables: {', '.join(missing_deliverables)}")
        
        if unexpected_changes:
            reasons.append(f"Unexpected changes: {', '.join(unexpected_changes)}")
        
        for file in self.changed_files:
            if self.is_runtime_artifact(file):
                warnings.append(f"Detected runtime artifact: {file}")

        return {
            "mergeable": in_scope_changed and not unexpected_changes,
            "reasons": sorted(reasons),
            "warnings": warnings,
        }

    @staticmethod
    def is_runtime_artifact(file: str) -> bool:
        return file.startswith("logs/") or file.endswith((".tmp", ".cache"))
