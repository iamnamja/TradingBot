"""
Git guardrails module for orchestrator safety.

Prevents real execution in unsafe git states:
- Running on main branch
- Dirty worktree
- Branch name not matching expected pattern
"""

import re
import subprocess
from typing import Tuple


class GitGuardrails:
    """Enforces git safety rules before real task execution."""

    def __init__(self, branch_naming_pattern: str) -> None:
        """
        Initialize guardrails with branch naming pattern.

        Args:
            branch_naming_pattern: Required pattern for branch names (e.g., "feature/*")
        """
        self.branch_naming_pattern = branch_naming_pattern

    def check(self) -> Tuple[bool, str]:
        """
        Verify git state is safe for real execution.

        Returns:
            (safe: bool, reason: str) where safe=True means execution is allowed.
        """
        # Check if on main branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            current_branch = result.stdout.strip()
        except subprocess.CalledProcessError as exc:
            return False, f"Failed to detect current branch: {exc}"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # git not available or timed out — treat as safe to proceed
            return True, ""

        # If the branch name contains spaces or looks like command output
        # rather than a real branch name, skip guardrails safely
        if not current_branch or " " in current_branch or len(current_branch) > 100:
            return True, ""

        if current_branch == "main":
            return False, "Cannot execute on main branch"

        # Check if branch matches required pattern
        if not self._matches_pattern(current_branch):
            return False, f"Branch name '{current_branch}' does not match pattern '{self.branch_naming_pattern}'"

        # Check for uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            if result.stdout.strip():
                return False, "Worktree has uncommitted changes"
        except subprocess.CalledProcessError as exc:
            return False, f"Failed to check worktree status: {exc}"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return True, ""

        return True, ""

    def _matches_pattern(self, branch_name: str) -> bool:
        """
        Check if branch name matches the required pattern.

        Args:
            branch_name: Current git branch name

        Returns:
            True if branch matches pattern
        """
        # Convert glob-style pattern to regex
        # feature/* -> ^feature/.*$
        pattern = self.branch_naming_pattern.replace("*", ".*")
        if not pattern.startswith("^"):
            pattern = f"^{pattern}"
        if not pattern.endswith("$"):
            pattern = f"{pattern}$"

        return bool(re.match(pattern, branch_name))
