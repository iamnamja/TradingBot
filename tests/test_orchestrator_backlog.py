import os
import pytest
from src.builder.orchestrator.backlog import BacklogTracker
from src.builder.orchestrator.state import TaskStatus, TaskMetadata

@pytest.fixture
def mock_tasks_directory(tmp_path):
    tasks = ["001_task_one.py", "002_task_two.py", "015_task_three.py"]
    for task in tasks:
        (tmp_path / task).touch()
    return tmp_path

def test_scan_tasks(mock_tasks_directory):
    tracker = BacklogTracker(mock_tasks_directory)
    tasks = tracker.scan_tasks()
    assert len(tasks) == 3
    assert tasks[0] == TaskMetadata(name="task_one.py", order=1, status=TaskStatus(status="pending"))
    assert tasks[1] == TaskMetadata(name="task_two.py", order=2, status=TaskStatus(status="pending"))
    assert tasks[2] == TaskMetadata(name="task_three.py", order=15, status=TaskStatus(status="pending"))

def test_get_next_task(mock_tasks_directory):
    tracker = BacklogTracker(mock_tasks_directory)
    tasks = tracker.scan_tasks()
    next_task = tracker.get_next_task(tasks)
    assert next_task == TaskMetadata(name="task_one.py", order=1, status=TaskStatus(status="pending"))

    # Simulate running the first task
    tasks[0] = TaskMetadata(name="task_one.py", order=1, status=TaskStatus(status="running"))
    next_task = tracker.get_next_task(tasks)
    assert next_task == TaskMetadata(name="task_two.py", order=2, status=TaskStatus(status="pending"))

def test_load_state(mock_tasks_directory):
    tracker = BacklogTracker(mock_tasks_directory)
    state_file = mock_tasks_directory / "state.json"
    tasks = tracker.scan_tasks()
    tracker.save_state(state_file, tasks)

    loaded_tasks = tracker.load_state(state_file)
    assert len(loaded_tasks) == 3
    assert loaded_tasks[0] == TaskMetadata(name="task_one.py", order=1, status=TaskStatus(status="pending"))

def test_save_state(mock_tasks_directory):
    tracker = BacklogTracker(mock_tasks_directory)
    state_file = mock_tasks_directory / "state.json"
    tasks = tracker.scan_tasks()
    tracker.save_state(state_file, tasks)

    assert os.path.exists(state_file)
