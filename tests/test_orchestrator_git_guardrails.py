"""
Tests for git guardrails module.

Verifies that real execution is blocked in unsafe git states:
- Running on main branch
- Dirty worktree
- Branch name not matching pattern
"""

import subprocess
from unittest.mock import MagicMock, patch


from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.git_guardrails import GitGuardrails
from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.state import OrchestratorState


class TestGitGuardrails:
    """Unit tests for GitGuardrails class."""

    def test_check_fails_on_main_branch(self):
        """Test that guardrails block execution on main branch."""
        guardrails = GitGuardrails(branch_naming_pattern="feature/*")

        with patch("subprocess.run") as mock_run:
            # Simulate being on main branch
            mock_run.return_value = MagicMock(
                stdout="main\n",
                returncode=0,
            )

            safe, reason = guardrails.check()

            assert safe is False
            assert "Cannot execute on main branch" in reason

    def test_check_fails_on_dirty_worktree(self):
        """Test that guardrails block execution with uncommitted changes."""
        guardrails = GitGuardrails(branch_naming_pattern="feature/*")

        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(stdout="feature/test-branch\n", returncode=0)
                elif "status" in cmd:
                    return MagicMock(stdout=" M file.py\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = side_effect

            safe, reason = guardrails.check()

            assert safe is False
            assert "uncommitted changes" in reason

    def test_check_fails_on_invalid_branch_pattern(self):
        """Test that guardrails block execution on branch not matching pattern."""
        guardrails = GitGuardrails(branch_naming_pattern="feature/*")

        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(stdout="bugfix/test-branch\n", returncode=0)
                elif "status" in cmd:
                    return MagicMock(stdout="", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = side_effect

            safe, reason = guardrails.check()

            assert safe is False
            assert "does not match pattern" in reason
            assert "bugfix/test-branch" in reason

    def test_check_passes_on_valid_branch(self):
        """Test that guardrails allow execution on valid clean branch."""
        guardrails = GitGuardrails(branch_naming_pattern="feature/*")

        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(stdout="feature/test-branch\n", returncode=0)
                elif "status" in cmd:
                    return MagicMock(stdout="", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = side_effect

            safe, reason = guardrails.check()

            assert safe is True
            assert reason == ""

    def test_check_handles_git_command_failure(self):
        """Test that guardrails handle git command failures gracefully."""
        guardrails = GitGuardrails(branch_naming_pattern="feature/*")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            safe, reason = guardrails.check()

            assert safe is False
            assert "Failed to detect current branch" in reason


class TestRunnerGuardrailIntegration:
    """Integration tests for guardrails in OrchestratorRunner."""

    def test_run_next_task_blocked_on_main_branch(self, tmp_path):
        """Test that run_next_task blocks execution on main branch."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "001_test_task.md").write_text("# Test Task")

        config = ProjectAdapter.get_tradingbot_default_config()
        config.tasks_directory = str(tasks_dir)

        backlog_tracker = BacklogTracker(tasks_directory=str(tasks_dir))
        runner = OrchestratorRunner(
            config=config,
            backlog_tracker=backlog_tracker,
            initial_state=OrchestratorState(tasks=[]),
        )

        with patch("builder.orchestrator.git_guardrails.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="main\n",
                returncode=0,
            )

            result = runner.run_next_task(dry_run=False)

            assert result["status"] == "blocked"
            assert result["outcome"] == "guardrail_failed"
            assert "main branch" in result["message"]
            assert result["task_name"] == "none"

    def test_run_next_task_blocked_on_dirty_worktree(self, tmp_path):
        """Test that run_next_task blocks execution with uncommitted changes."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "001_test_task.md").write_text("# Test Task")

        config = ProjectAdapter.get_tradingbot_default_config()
        config.tasks_directory = str(tasks_dir)

        backlog_tracker = BacklogTracker(tasks_directory=str(tasks_dir))
        runner = OrchestratorRunner(
            config=config,
            backlog_tracker=backlog_tracker,
            initial_state=OrchestratorState(tasks=[]),
        )

        with patch("builder.orchestrator.git_guardrails.subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(stdout="feature/test-branch\n", returncode=0)
                elif "status" in cmd:
                    return MagicMock(stdout=" M file.py\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = side_effect

            result = runner.run_next_task(dry_run=False)

            assert result["status"] == "blocked"
            assert result["outcome"] == "guardrail_failed"
            assert "uncommitted changes" in result["message"]

    def test_run_next_task_blocked_on_invalid_branch(self, tmp_path):
        """Test that run_next_task blocks execution on invalid branch name."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "001_test_task.md").write_text("# Test Task")

        config = ProjectAdapter.get_tradingbot_default_config()
        config.tasks_directory = str(tasks_dir)

        backlog_tracker = BacklogTracker(tasks_directory=str(tasks_dir))
        runner = OrchestratorRunner(
            config=config,
            backlog_tracker=backlog_tracker,
            initial_state=OrchestratorState(tasks=[]),
        )

        with patch("builder.orchestrator.git_guardrails.subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(stdout="bugfix/test-branch\n", returncode=0)
                elif "status" in cmd:
                    return MagicMock(stdout="", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = side_effect

            result = runner.run_next_task(dry_run=False)

            assert result["status"] == "blocked"
            assert result["outcome"] == "guardrail_failed"
            assert "does not match pattern" in result["message"]

    def test_run_next_task_allowed_on_valid_branch(self, tmp_path):
        """Test that run_next_task proceeds on valid clean branch."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "001_test_task.md").write_text("# Test Task")

        config = ProjectAdapter.get_tradingbot_default_config()
        config.tasks_directory = str(tasks_dir)

        backlog_tracker = BacklogTracker(tasks_directory=str(tasks_dir))
        runner = OrchestratorRunner(
            config=config,
            backlog_tracker=backlog_tracker,
            initial_state=OrchestratorState(tasks=[]),
        )

        with patch("builder.orchestrator.git_guardrails.subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(stdout="feature/test-branch\n", returncode=0)
                elif "status" in cmd:
                    return MagicMock(stdout="", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = side_effect

            result = runner.run_next_task(dry_run=False)

            assert result["status"] == "running"
            assert result["outcome"] == "ready_for_pr"

    def test_dry_run_bypasses_guardrails(self, tmp_path):
        """Test that dry_run mode bypasses guardrails."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "001_test_task.md").write_text("# Test Task")

        config = ProjectAdapter.get_tradingbot_default_config()
        config.tasks_directory = str(tasks_dir)

        backlog_tracker = BacklogTracker(tasks_directory=str(tasks_dir))
        runner = OrchestratorRunner(
            config=config,
            backlog_tracker=backlog_tracker,
            initial_state=OrchestratorState(tasks=[]),
        )

        with patch("builder.orchestrator.git_guardrails.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="main\n",
                returncode=0,
            )

            result = runner.run_next_task(dry_run=True)

            assert result["status"] == "planned"
            assert result["dry_run"] is True

    def test_simulate_bypasses_guardrails(self, tmp_path):
        """Test that simulate_backlog mode bypasses guardrails."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "001_test_task.md").write_text("# Test Task")

        config = ProjectAdapter.get_tradingbot_default_config()
        config.tasks_directory = str(tasks_dir)

        backlog_tracker = BacklogTracker(tasks_directory=str(tasks_dir))
        runner = OrchestratorRunner(
            config=config,
            backlog_tracker=backlog_tracker,
            initial_state=OrchestratorState(tasks=[]),
        )

        # Mock execute_task to avoid real subprocess and mock get_next_task
        # so simulate_backlog sequences correctly via side_effect
        from unittest.mock import MagicMock, patch
        runner.execute_task = MagicMock(return_value={
            "success": True,
            "output": "Task executed successfully",
            "changed_files": [],
        })
        backlog_tracker.get_next_task = MagicMock(side_effect=[
            TaskMetadata(name="test_task.md", order=1, status=TaskStatus(status="pending")),
            None,
        ])

        result = runner.simulate_backlog()

        assert result["final_status"] == "completed"
        assert len(result["processed_tasks"]) == 1

    def test_skip_guardrails_flag(self, tmp_path):
        """Test that --skip-guardrails flag disables guardrails."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "001_test_task.md").write_text("# Test Task")

        config = ProjectAdapter.get_tradingbot_default_config()
        config.tasks_directory = str(tasks_dir)

        backlog_tracker = BacklogTracker(tasks_directory=str(tasks_dir))
        runner = OrchestratorRunner(
            config=config,
            backlog_tracker=backlog_tracker,
            initial_state=OrchestratorState(tasks=[]),
        )
        runner.skip_guardrails = True

        with patch("builder.orchestrator.git_guardrails.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="main\n",
                returncode=0,
            )

            result = runner.run_next_task(dry_run=False)

            assert result["status"] == "running"
            assert result["outcome"] == "ready_for_pr"
