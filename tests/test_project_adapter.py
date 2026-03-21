from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.project_config import ProjectConfig


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
    assert config.state_path is None
    assert config.task_file_pattern == "*.md"
    assert config.audit_path is None


def test_generic_project_config_defaults():
    config = ProjectAdapter.get_generic_project_config()
    assert config.tasks_directory == "generic_tasks/"
    assert config.lint_command == "flake8 ."
    assert config.test_command == "pytest tests/test_generic.py"
    assert config.branch_naming_pattern == "feature/generic/*"
    assert config.protected_file_patterns == ["*.tmp"]
    assert config.artifact_path_patterns == ["generic_artifacts/*"]
    assert config.approval_required_file_patterns == ["README.md"]
    assert config.task_runner_command is None
    assert config.state_path is None
    assert config.task_file_pattern == "*.task.md"
    assert config.audit_path is None


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
        state_path=None,
        task_file_pattern="*.md",
        audit_path=None,
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
    assert behavior["state_path"] is None
    assert behavior["task_file_pattern"] == "*.md"
    assert behavior["audit_path"] is None


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
        state_path="state.json",
        task_file_pattern="*.md",
        audit_path="audit.log",
    )
    adapter = ProjectAdapter(config=project_config)
    behavior = adapter.translate_to_orchestrator_behavior()

    assert behavior["task_runner_command"] == "python"
    assert behavior["state_path"] == "state.json"
    assert behavior["task_file_pattern"] == "*.md"
    assert behavior["audit_path"] == "audit.log"


def test_config_is_mutable():
    config = ProjectAdapter.get_tradingbot_default_config()
    config.task_runner_command = "python"
    config.state_path = "state.json"
    config.task_file_pattern = "*.task.md"
    config.audit_path = "audit.log"
    assert config.task_runner_command == "python"
    assert config.state_path == "state.json"
    assert config.task_file_pattern == "*.task.md"
    assert config.audit_path == "audit.log"


def test_factory_methods_still_exist():
    assert hasattr(ProjectAdapter, "get_tradingbot_default_config")
    assert hasattr(ProjectAdapter, "get_generic_project_config")


def test_generic_and_tradingbot_configs_are_distinct():
    tradingbot = ProjectAdapter.get_tradingbot_default_config()
    generic = ProjectAdapter.get_generic_project_config()

    assert generic.tasks_directory != tradingbot.tasks_directory
    assert generic.branch_naming_pattern != tradingbot.branch_naming_pattern
    assert generic.task_file_pattern != tradingbot.task_file_pattern
