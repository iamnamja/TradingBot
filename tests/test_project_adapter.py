from builder.orchestrator.project_config import ProjectConfig
from builder.orchestrator.project_adapter import ProjectAdapter

def test_tradingbot_default_config():
    config = ProjectAdapter.get_tradingbot_default_config()
    assert config.tasks_directory == "tasks/"
    assert config.lint_command == "ruff check ."
    assert config.test_command == "pytest -q"
    assert config.branch_naming_pattern == "feature/*"
    assert config.protected_file_patterns == ["*.pyc", "*.log"]
    assert config.artifact_path_patterns == ["artifacts/*"]
    assert config.approval_required_file_patterns == ["README.md", "CHANGELOG.md"]
    assert config.task_runner_command is None

def test_translate_to_orchestrator_behavior():
    project_config = ProjectConfig(
        tasks_directory="tasks/",
        lint_command="ruff check .",
        test_command="pytest -q",
        branch_naming_pattern="feature/*",
        protected_file_patterns=["*.pyc", "*.log"],
        artifact_path_patterns=["artifacts/*"],
        approval_required_file_patterns=["README.md", "CHANGELOG.md"],
        task_runner_command=None,
    )
    adapter = ProjectAdapter(config=project_config)
    behavior = adapter.translate_to_orchestrator_behavior()
    
    assert behavior["tasks_directory"] == "tasks/"
    assert behavior["lint_command"] == "ruff check ."
    assert behavior["test_command"] == "pytest -q"
    assert behavior["branch_naming_pattern"] == "feature/*"
    assert behavior["protected_file_patterns"] == ["*.pyc", "*.log"]
    assert behavior["artifact_path_patterns"] == ["artifacts/*"]
    assert behavior["approval_required_file_patterns"] == ["README.md", "CHANGELOG.md"]
    assert behavior["task_runner_command"] is None

def test_translate_to_orchestrator_behavior_with_real_command():
    project_config = ProjectConfig(
        tasks_directory="tasks/",
        lint_command="ruff check .",
        test_command="pytest -q",
        branch_naming_pattern="feature/*",
        protected_file_patterns=["*.pyc", "*.log"],
        artifact_path_patterns=["artifacts/*"],
        approval_required_file_patterns=["README.md", "CHANGELOG.md"],
        task_runner_command="python",
    )
    adapter = ProjectAdapter(config=project_config)
    behavior = adapter.translate_to_orchestrator_behavior()
    
    assert behavior["task_runner_command"] == "python"

def test_config_is_mutable():
    config = ProjectAdapter.get_tradingbot_default_config()
    config.task_runner_command = "python"
    assert config.task_runner_command == "python"
