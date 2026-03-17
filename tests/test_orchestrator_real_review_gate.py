from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.state import OrchestratorState
from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.policy import PolicyEngine


def test_mergeable_success():
    """Test that execution with valid changed files becomes ready_for_pr."""
    config = ProjectAdapter.get_tradingbot_default_config()
    config.approval_required_file_patterns = []
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(
        config=config, backlog_tracker=backlog_tracker, initial_state=initial_state
    )

    runner.run_review = lambda changed_files: {"mergeable": True}

    execution_result = {
        "success": True,
        "status": "success",
        "output": "Task executed successfully",
        "failure_text": "",
        "changed_files": ["file1.py"],
        "deliverables_updated": ["file1.py"],
        "raw_stdout": "",
        "raw_stderr": "",
        "returncode": 0,
    }

    from builder.orchestrator.state import TaskMetadata, TaskStatus

    task = TaskMetadata(name="test_task", order=1, status=TaskStatus(status="running"))

    result = runner.process_execution_result(execution_result, task)

    assert result["outcome"] == "ready_for_pr"
    assert result["next_action"] == "merge"
    assert result["requires_approval"] is False


def test_missing_deliverables():
    """Test that missing deliverables blocks review."""
    config = ProjectAdapter.get_tradingbot_default_config()
    config.approval_required_file_patterns = []
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(
        config=config, backlog_tracker=backlog_tracker, initial_state=initial_state
    )

    execution_result = {
        "success": True,
        "status": "success",
        "output": "Task executed successfully",
        "failure_text": "",
        "changed_files": ["other_file.py"],
        "deliverables_updated": [],
        "raw_stdout": "",
        "raw_stderr": "",
        "returncode": 0,
    }

    from builder.orchestrator.state import TaskMetadata, TaskStatus

    task = TaskMetadata(name="test_task", order=1, status=TaskStatus(status="running"))

    result = runner.process_execution_result(execution_result, task)

    assert result["outcome"] == "review_blocked"
    assert result["next_action"] == "requires_approval"
    assert result["requires_approval"] is True


def test_approval_required_file_changes():
    """Test that changes to approval-required files block review."""
    config = ProjectAdapter.get_tradingbot_default_config()
    config.approval_required_file_patterns = ["README.md"]
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(
        config=config, backlog_tracker=backlog_tracker, initial_state=initial_state
    )

    execution_result = {
        "success": True,
        "status": "success",
        "output": "Task executed successfully",
        "failure_text": "",
        "changed_files": ["README.md"],
        "deliverables_updated": ["README.md"],
        "raw_stdout": "",
        "raw_stderr": "",
        "returncode": 0,
    }

    from builder.orchestrator.state import TaskMetadata, TaskStatus

    task = TaskMetadata(name="test_task", order=1, status=TaskStatus(status="running"))

    result = runner.process_execution_result(execution_result, task)

    assert result["outcome"] == "review_blocked"
    assert result["next_action"] == "requires_approval"
    assert result["requires_approval"] is True


def test_no_changed_files_edge_case():
    """Test that execution with no changed files passes review."""
    config = ProjectAdapter.get_tradingbot_default_config()
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(
        config=config, backlog_tracker=backlog_tracker, initial_state=initial_state
    )

    execution_result = {
        "success": True,
        "status": "success",
        "output": "Task executed successfully",
        "failure_text": "",
        "changed_files": [],
        "deliverables_updated": [],
        "raw_stdout": "",
        "raw_stderr": "",
        "returncode": 0,
    }

    from builder.orchestrator.state import TaskMetadata, TaskStatus

    task = TaskMetadata(name="test_task", order=1, status=TaskStatus(status="running"))

    result = runner.process_execution_result(execution_result, task)

    assert result["outcome"] == "ready_for_pr"
    assert result["next_action"] == "merge"
    assert result["requires_approval"] is False


def test_policy_engine_requires_approval():
    """Test PolicyEngine.requires_approval method."""
    policy = PolicyEngine(
        approval_required_file_patterns=["README.md", "CHANGELOG.md"],
        protected_file_patterns=["protected_file.py"],
    )

    assert policy.requires_approval(["README.md"]) is True
    assert policy.requires_approval(["CHANGELOG.md"]) is True
    assert policy.requires_approval(["some_file.py"]) is False
    assert policy.requires_approval([]) is False
