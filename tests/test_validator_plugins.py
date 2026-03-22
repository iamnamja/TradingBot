
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _load_modules() -> tuple[Any, Any, Any, Any]:
    root = Path(__file__).resolve().parents[1]
    for candidate in (root, root / "src"):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    run_task = importlib.import_module("agents.run_task")
    validator_runner = importlib.import_module("agents.lib.validator_runner")
    project_adapter = importlib.import_module("builder.orchestrator.project_adapter")
    project_config = importlib.import_module("builder.orchestrator.project_config")
    return run_task, validator_runner, project_adapter, project_config


def _base_config(project_config_module: Any):
    return project_config_module.ProjectConfig(
        tasks_directory="tasks/",
        lint_command="ruff check .",
        test_command="pytest -q",
        branch_naming_pattern="feature/*",
        protected_file_patterns=[],
        artifact_path_patterns=[],
        approval_required_file_patterns=[],
        validators=None,
    )


def test_plugin_validator_non_pytest_path_runs(monkeypatch) -> None:
    _, validator_runner, _, project_config_module = _load_modules()
    cfg = _base_config(project_config_module)
    cfg.validators = [
        {"name": "cli_smoke", "command": ["python", "-c", "print('smoke')"], "enabled": True, "required": True}
    ]

    calls: list[Any] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(validator_runner.subprocess, "run", fake_run)
    ok, output = validator_runner.run_checks(cfg)

    assert ok is True
    assert calls == [["python", "-c", "print('smoke')"]]
    assert "[cli_smoke] ok" in output


def test_plugin_selection_is_adapter_driven() -> None:
    _, validator_runner, project_adapter_module, project_config_module = _load_modules()
    cfg = _base_config(project_config_module)
    cfg.validators = [{"name": "snapshot", "command": ["snapshot-check"], "enabled": True, "required": False}]
    adapter = project_adapter_module.ProjectAdapter(cfg)
    behavior = adapter.translate_to_orchestrator_behavior()

    assert behavior["validators"][0]["name"] == "snapshot"
    selected = validator_runner.select_validators(cfg)
    assert selected[0].name == "snapshot"


def test_run_task_wrapper_delegates(monkeypatch) -> None:
    run_task, validator_runner, _, _ = _load_modules()

    def fake_run_checks(*args, **kwargs):
        return True, "delegated"

    monkeypatch.setattr(validator_runner, "run_checks", fake_run_checks)
    ok, text = run_task.run_checks()

    assert ok is True
    assert text == "delegated"
