from unittest.mock import patch
import pytest
from builder.orchestrator.merge import MergeManager

@pytest.fixture
def merge_manager():
    return MergeManager(repo_name="test_repo", branch_name="test_branch")

def test_create_pr(merge_manager):
    title = "Test PR"
    body = "This is a test PR."
    result = merge_manager.create_pr(title, body)
    assert result == "PR created: Test PR"

def test_wait_for_ci(merge_manager):
    result = merge_manager.wait_for_ci()
    assert result is True

def test_merge_pr_pass(merge_manager):
    result = merge_manager.merge_pr()
    assert result == "PR merged successfully."

def test_merge_pr_fail(merge_manager):
    with patch.object(merge_manager, 'wait_for_ci', return_value=False):
        with pytest.raises(Exception, match="CI failed, cannot merge."):
            merge_manager.merge_pr()

def test_sync_main(merge_manager):
    result = merge_manager.sync_main()
    assert result == "Local main branch synced."
