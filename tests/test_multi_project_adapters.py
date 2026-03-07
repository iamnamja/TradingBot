from builder.orchestrator.project_adapter import ProjectAdapter

def test_tradingbot_adapter():
    config = ProjectAdapter.get_tradingbot_default_config()
    assert config.tasks_directory == "tasks/"
    assert config.lint_command == "ruff check ."
    assert config.test_command == "pytest -q"

def test_generic_adapter():
    config = ProjectAdapter.get_generic_project_config()
    assert config.tasks_directory == "generic_tasks/"
    assert config.lint_command == "flake8 ."
    assert config.test_command == "pytest tests/test_generic.py"
