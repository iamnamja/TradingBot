from __future__ import annotations

from .command_runner import CommandRunner


class MergeManager:
    def __init__(
        self,
        repo_name: str,
        branch_name: str,
        command_runner: CommandRunner | None = None,
    ):
        self.repo_name = repo_name
        self.branch_name = branch_name
        self.command_runner = command_runner or CommandRunner()

    def create_pr(self, title: str, body: str) -> str:
        command = f'gh pr create --title "{title}" --body "{body}"'
        result = self.command_runner.execute(command)
        if result["returncode"] != 0:
            raise Exception(f'Failed to create PR: {result["stderr"]}')
        return f"PR created: {title}"

    def wait_for_ci(self) -> str:
        command = "gh pr checks"
        result = self.command_runner.execute(command)
        if result["returncode"] != 0:
            raise Exception(f'Failed to check CI status: {result["stderr"]}')

        ci_status = (result.get("stdout") or "").strip().lower()
        if "pending" in ci_status:
            return "pending"
        if "failed" in ci_status or "error" in ci_status:
            return "failed"
        return "passed"

    def merge_pr(self) -> str:
        ci_status = self.wait_for_ci()
        if ci_status == "failed":
            raise Exception("CI failed, cannot merge.")
        if ci_status == "pending":
            raise Exception("CI is still pending, cannot merge.")

        command = "gh pr merge"
        result = self.command_runner.execute(command)
        if result["returncode"] != 0:
            raise Exception(f'Failed to merge PR: {result["stderr"]}')
        return "PR merged successfully."

    def sync_main(self) -> str:
        command = "git switch main && git pull"
        result = self.command_runner.execute(command)
        if result["returncode"] != 0:
            raise Exception(f'Failed to sync main branch: {result["stderr"]}')
        return "Local main branch synced."
