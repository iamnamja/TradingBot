
class MergeManager:
    def __init__(self, repo_name: str, branch_name: str):
        self.repo_name = repo_name
        self.branch_name = branch_name

    def create_pr(self, title: str, body: str) -> str:
        # Simulate PR creation
        return f"PR created: {title}"

    def wait_for_ci(self) -> bool:
        # Simulate CI polling
        return True  # Assume CI passes for this simulation

    def merge_pr(self) -> str:
        if not self.wait_for_ci():
            raise Exception("CI failed, cannot merge.")
        # Simulate merge decision
        return "PR merged successfully."

    def sync_main(self) -> str:
        # Simulate syncing local main branch
        return "Local main branch synced."
