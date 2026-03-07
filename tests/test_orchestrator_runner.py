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
        TaskMetadata(name="002_task.py", order=2, status=TaskStatus(status="pending")),
    ]
    tracker.get_next_task.return_value = tracker.scan_tasks.return_value[0]
    return tracker

@pytest.fixture
def initial_state():
    return OrchestratorState(tasks=[])

def test_orchestrator_runner_selects_next_task(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    next_task = runner.select_next_task()
    
    assert next_task.name == "001_task.py"
    assert next_task.status.status == "pending"

def test_orchestrator_runner_runs_next_task(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    result = runner.run_next_task()
    
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "running"
    assert result['message'] == "Task is now running."

def test_orchestrator_runner_no_pending_tasks(mock_backlog_tracker, initial_state):
    mock_backlog_tracker.get_next_task.return_value = None
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    result = runner.run_next_task()
    
    assert result['task_name'] == "none"
    assert result['status'] == "no_task"
    assert result['message'] == "No pending tasks available."
