from __future__ import annotations

import shutil
from pathlib import Path

from builder.orchestrator.project_adapter import load_project_adapter
from builder.orchestrator.project_config import load_project_config


def test_second_project_fixture_config_and_adapter_are_portable(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_app")
    project_root = tmp_path / "copied_sample_app"
    shutil.copytree(fixture_root, project_root)

    config = load_project_config(project_root / "project_config.json")
    adapter = load_project_adapter(project_root)
    behavior = adapter.translate_to_orchestrator_behavior()

    assert config.tasks_directory == "tasks/"
    assert (project_root / config.tasks_directory / "001_sample_task.md").exists()
    assert "TradingBot" not in str(project_root)

    assert behavior["branch_naming_pattern"] == "work/*"
    assert behavior["protected_file_patterns"] == ["secrets/*.key", "deploy/prod.env"]

    validators = behavior["validators"]
    assert isinstance(validators, list)
    assert [validator["name"] for validator in validators] == ["compile", "sample-tests"]
    assert validators[0]["command"] == "python -m py_compile src/sample_app/main.py"
