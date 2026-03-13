import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.state import OrchestratorState, TaskMetadata, TaskStatus
from builder.orchestrator.project_adapter import ProjectAdapter

@pytest.fixture
def config_with_real_execution():
    config = ProjectAdapter.get_tradingbot_default_config()
    config.task_runner_command = sys.executable
    return config

@pytest.fixture
def mock_backlog_tracker():
    tracker = MagicMock(spec=BacklogTracker)
    tracker.scan_tasks.return_value = [
        TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending")),
    ]
    tracker.get_next_task.return_value = tracker.scan_tasks.return_value[0]
    return tracker

@pytest.fixture
def initial_state():
    return OrchestratorState(tasks=[])

def test_execute_task_with_real_command(config_with_real_execution, initial_state):
    tracker = MagicMock(spec=BacklogTracker)
    runner = OrchestratorRunner(config_with_real_execution, tracker, initial_state)
    
    task = TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending"))
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Task executed successfully\n",
            stderr="",
        )
        
        result = runner.execute_task(task)
        
        assert result["success"] is True
        assert result["status"] == "success"
        assert result["stdout"] == "Task executed successfully"
        assert result["stderr"] == ""
        assert result["returncode"] == 0
        assert "001_task.py" in result["task_file"]
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == sys.executable
        assert Path(call_args[0][0][1]).name == "001_task.py"

def test_execute_task_with_real_command_failure(config_with_real_execution, initial_state):
    tracker = MagicMock(spec=BacklogTracker)
    runner = OrchestratorRunner(config_with_real_execution, tracker, initial_state)
    
    task = TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending"))
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Task execution failed\n",
        )
        
        result = runner.execute_task(task)
        
        assert result["success"] is False
        assert result["status"] == "failure"
        assert result["stdout"] == ""
        assert result["stderr"] == "Task execution failed"
        assert result["returncode"] == 1
        assert "001_task.py" in result["task_file"]

def test_execute_task_without_real_command(initial_state):
    config = ProjectAdapter.get_tradingbot_default_config()
    tracker = MagicMock(spec=BacklogTracker)
    runner = OrchestratorRunner(config, tracker, initial_state)
    
    task = TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending"))
    
    result = runner.execute_task(task)
    
    assert result["success"] is True
    assert result["changed_files"] == []

def test_run_next_task_with_real_execution_success(config_with_real_execution, mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(config_with_real_execution, mock_backlog_tracker, initial_state)
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Task executed successfully\n",
            stderr="",
        )
        
        result = runner.run_next_task()
        
        assert result["task_name"] == "001_task.py"
        assert result["status"] == "running"
        assert result["message"] == "Task is now running."
        assert result["outcome"] == "ready_for_pr"
        assert result["next_action"] == "merge"
        assert result["requires_approval"] is False

def test_run_next_task_with_real_execution_failure(config_with_real_execution, mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(config_with_real_execution, mock_backlog_tracker, initial_state)
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Task execution failed\n",
        )
        
        result = runner.run_next_task()
        
        assert result["task_name"] == "001_task.py"
        assert result["status"] == "failed"
        assert "Task execution failed" in result["message"]
        assert result["outcome"] == "repair_required"
        assert result["next_action"] == "require_human_review"
        assert result["requires_approval"] is True

def test_config_mutability():
    config = ProjectAdapter.get_tradingbot_default_config()
    config.task_runner_command = sys.executable
    assert config.task_runner_command == sys.executable
