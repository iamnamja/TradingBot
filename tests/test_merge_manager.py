from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from builder.orchestrator.merge import MergeManager


@pytest.fixture
def mock_command_runner():
    runner = MagicMock()
    runner.execute.return_value = {"returncode": 0, "stdout": "passed", "stderr": ""}
    return runner


@pytest.fixture
def merge_manager(mock_command_runner):
    return MergeManager(
        repo_name="test_repo",
        branch_name="test_branch",
        command_runner=mock_command_runner,
    )


def test_create_pr(merge_manager, mock_command_runner):
    title = "Test PR"
    body = "This is a test PR."

    result = merge_manager.create_pr(title, body)

    assert result == "PR created: Test PR"
    mock_command_runner.execute.assert_called_once()


def test_wait_for_ci_passed(merge_manager, mock_command_runner):
    mock_command_runner.execute.return_value = {
        "returncode": 0,
        "stdout": "passed",
        "stderr": "",
    }

    result = merge_manager.wait_for_ci()

    assert result == "passed"


def test_wait_for_ci_pending(merge_manager, mock_command_runner):
    mock_command_runner.execute.return_value = {
        "returncode": 0,
        "stdout": "pending",
        "stderr": "",
    }

    result = merge_manager.wait_for_ci()

    assert result == "pending"


def test_merge_pr_pass(merge_manager):
    with patch.object(merge_manager, "wait_for_ci", return_value="passed"):
        result = merge_manager.merge_pr()
        assert result == "PR merged successfully."


def test_merge_pr_fail(merge_manager):
    with patch.object(merge_manager, "wait_for_ci", return_value="failed"):
        with pytest.raises(Exception, match="CI failed, cannot merge."):
            merge_manager.merge_pr()


def test_sync_main(merge_manager):
    result = merge_manager.sync_main()
    assert result == "Local main branch synced."
