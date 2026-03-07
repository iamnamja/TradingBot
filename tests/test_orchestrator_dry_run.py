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

def test_orchestrator_runner_dry_run(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    result = runner.run_next_task(dry_run=True)
    
    assert result['dry_run'] is True
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "planned"
    assert result['message'] == "Task is planned for execution."

def test_orchestrator_runner_no_pending_tasks_dry_run(mock_backlog_tracker, initial_state):
    mock_backlog_tracker.get_next_task.return_value = None
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    result = runner.run_next_task(dry_run=True)
    
    assert result['dry_run'] is True
    assert result['task_name'] == "none"
    assert result['status'] == "no_task"
    assert result['message'] == "No pending tasks available."
