import pytest
from builder.orchestrator.approval import create_approval_checkpoint
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.state import OrchestratorState, TaskMetadata, TaskStatus
from builder.orchestrator.project_adapter import ProjectAdapter

@pytest.fixture
def mock_backlog_tracker():
    tracker = BacklogTracker(tasks_directory="mock/tasks")
    return tracker

@pytest.fixture
def initial_state():
    return OrchestratorState(tasks=[])

def test_create_approval_checkpoint():
    checkpoint = create_approval_checkpoint("test_task", "Test reason", "policy", "merge")
    assert checkpoint["task_name"] == "test_task"
    assert checkpoint["reason"] == "Test reason"
    assert checkpoint["source"] == "policy"
    assert checkpoint["requested_action"] == "merge"
    assert checkpoint["status"] == "pending"
    assert checkpoint["requires_approval"] is True

def test_runner_stops_for_approval(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    mock_backlog_tracker.scan_tasks = lambda: [TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending"))]
    mock_backlog_tracker.get_next_task = lambda tasks: tasks[0]

    result = runner.run_next_task()
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "running"
    assert result['message'] == "Task is now running."
    
    # Simulate a review block
    runner.run_review = lambda changed_files: {"mergeable": False}
    result = runner.process_execution_result({"success": True, "changed_files": []}, TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="running")))
    
    assert result['requires_approval'] is True
    assert result['outcome'] == "review_blocked"
    assert result['next_action'] == "requires_approval"

def test_runner_no_approval_needed(mock_backlog_tracker, initial_state):
    runner = OrchestratorRunner(ProjectAdapter.get_tradingbot_default_config(), mock_backlog_tracker, initial_state)
    mock_backlog_tracker.scan_tasks = lambda: [TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="pending"))]
    mock_backlog_tracker.get_next_task = lambda tasks: tasks[0]

    result = runner.run_next_task()
    assert result['task_name'] == "001_task.py"
    assert result['status'] == "running"
    assert result['message'] == "Task is now running."
    
    # Simulate a successful review
    runner.run_review = lambda changed_files: {"mergeable": True}
    result = runner.process_execution_result({"success": True, "changed_files": []}, TaskMetadata(name="001_task.py", order=1, status=TaskStatus(status="running")))
    
    assert result['requires_approval'] is False
    assert result['outcome'] == "ready_for_pr"
    assert result['next_action'] == "merge"
