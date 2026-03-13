from builder.orchestrator.project_adapter import ProjectAdapter

def test_tradingbot_adapter():
    config = ProjectAdapter.get_tradingbot_default_config()
    assert config.tasks_directory == "tasks/"
    assert config.lint_command == "ruff check ."
    assert config.test_command == "pytest -q"
    assert config.task_runner_command is None

def test_generic_adapter():
    config = ProjectAdapter.get_generic_project_config()
    assert config.tasks_directory == "generic_tasks/"
    assert config.lint_command == "flake8 ."
    assert config.test_command == "pytest tests/test_generic.py"
    assert config.task_runner_command is None

def test_adapter_backward_compatibility():
    config = ProjectAdapter.get_tradingbot_default_config()
    adapter = ProjectAdapter(config=config)
    behavior = adapter.translate_to_orchestrator_behavior()
    
    assert "task_runner_command" in behavior
    assert behavior["task_runner_command"] is None

def test_generic_config_mutability():
    config = ProjectAdapter.get_generic_project_config()
    config.task_runner_command = "python"
    assert config.task_runner_command == "python"
