import pytest
from unittest.mock import MagicMock
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

def test_orchestrator_runner_simulate(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    
    # Simulate successful execution of all tasks
    mock_backlog_tracker.get_next_task.side_effect = [
        TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending")),
        TaskMetadata(name="002_task.py", order=2, status=TaskStatus(status="pending")),
        None  # No more tasks
    ]
    
    runner.execute_task = MagicMock(return_value={"success": True, "changed_files": []})
    runner.run_review = MagicMock(return_value={"mergeable": True})

    simulation_result = runner.simulate_backlog()
    
    assert simulation_result['processed_tasks'] == ["001_task.py", "002_task.py"]
    assert simulation_result['stopped_reason'] == ""
    assert simulation_result['final_status'] == "completed"
    assert simulation_result['approval_required'] is False
    assert simulation_result['planned_actions'] == ["Task 001_task.py completed successfully.", "Task 002_task.py completed successfully."]

def test_orchestrator_runner_simulate_with_approval(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    
    # Simulate approval required on the second task
    mock_backlog_tracker.get_next_task.side_effect = [
        TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending")),
        TaskMetadata(name="002_task.py", order=2, status=TaskStatus(status="pending")),
        None  # No more tasks
    ]
    
    runner.execute_task = MagicMock(return_value={"success": True, "changed_files": []})
    runner.run_review = MagicMock(return_value={"mergeable": False})

    simulation_result = runner.simulate_backlog()
    
    assert simulation_result['processed_tasks'] == ["001_task.py", "002_task.py"]
    assert simulation_result['stopped_reason'] == "Approval required"
    assert simulation_result['final_status'] == "blocked"
    assert simulation_result['approval_required'] is True
    assert simulation_result['planned_actions'] == []

def test_orchestrator_runner_simulate_with_failure(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    
    # Simulate failure on the first task
    mock_backlog_tracker.get_next_task.side_effect = [
        TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending")),
        None  # No more tasks
    ]
    
    runner.execute_task = MagicMock(return_value={"success": False, "failure_text": "Execution failed"})
    
    simulation_result = runner.simulate_backlog()
    
    assert simulation_result['processed_tasks'] == ["001_task.py"]
    assert simulation_result['stopped_reason'] == "Execution failed"
    assert simulation_result['final_status'] == "failed"
    assert simulation_result['approval_required'] is False
    assert simulation_result['planned_actions'] == []

def test_orchestrator_runner_simulate_empty_backlog(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    
    # Simulate empty backlog
    mock_backlog_tracker.get_next_task.return_value = None

    simulation_result = runner.simulate_backlog()
    
    assert simulation_result['processed_tasks'] == []
    assert simulation_result['stopped_reason'] == ""
    assert simulation_result['final_status'] == "completed"
    assert simulation_result['approval_required'] is False
    assert simulation_result['planned_actions'] == []
