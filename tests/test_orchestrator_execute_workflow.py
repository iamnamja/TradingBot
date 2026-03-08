from unittest.mock import MagicMock
import pytest
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.state import OrchestratorState, TaskMetadata, TaskStatus
from builder.orchestrator.project_adapter import ProjectAdapter

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

def test_orchestrator_runner_no_pending_tasks(mock_backlog_tracker, initial_state):
    mock_backlog_tracker.get_next_task.return_value = None
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    result = runner.run_next_task()
    
    assert result['task_name'] == "none"
    assert result['status'] == "no_task"
    assert result['message'] == "No pending tasks available."
    assert result['outcome'] == "noop"
    assert result['next_action'] == "none"
    assert result['requires_approval'] is False

def test_orchestrator_runner_dry_run(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    result = runner.run_next_task(dry_run=True)
    
    assert result['dry_run'] is True
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "planned"
    assert result['message'] == "Task is planned for execution."
    assert result['outcome'] == "noop"
    assert result['next_action'] == "none"
    assert result['requires_approval'] is False

def test_orchestrator_runner_execution_success(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    result = runner.run_next_task()
    
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "running"
    assert result['message'] == "Task is now running."
    assert result['outcome'] == "ready_for_pr"
    assert result['next_action'] == "merge"
    assert result['requires_approval'] is False

def test_orchestrator_runner_execution_review_blocked(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    runner.run_review = MagicMock(return_value={"mergeable": False})
    result = runner.run_next_task()
    
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "running"
    assert result['message'] == "Task is now running."
    assert result['outcome'] == "review_blocked"
    assert result['next_action'] == "requires_approval"
    assert result['requires_approval'] is True

def test_orchestrator_runner_execution_failure(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    runner.execute_task = MagicMock(return_value={"success": False, "failure_text": "Execution failed"})
    result = runner.run_next_task()
    
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "failed"
    assert result['message'] == "Execution failed: Execution failed"
    assert result['outcome'] == "repair_required"
    assert result['next_action'] == "require_human_review"
    assert result['requires_approval'] is True
