from __future__ import annotations

from dataclasses import dataclass

from agents.lib import validator_runner
from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.project_config import ProjectConfig
import agents.run_task as run_task


@dataclass
class _CP:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def _base_config() -> ProjectConfig:
    return ProjectConfig(
        tasks_directory="tasks/",
        lint_command="ruff check .",
        test_command="pytest -q",
        branch_naming_pattern="feature/*",
        protected_file_patterns=[],
        artifact_path_patterns=[],
        approval_required_file_patterns=[],
        validators=None,
    )


def test_plugin_validator_non_pytest_path_runs(monkeypatch):
    cfg = _base_config()
    cfg.validators = [
        {"name": "cli_smoke", "command": "python -c \"print('smoke')\"", "enabled": True, "required": True}
    ]

    calls: list[str] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return _CP(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(validator_runner.subprocess, "run", fake_run)
    ok, output = validator_runner.run_checks(cfg)

    assert ok
    assert calls == ["python -c \"print('smoke')\""]
    assert "[cli_smoke] ok" in output


def test_plugin_selection_is_adapter_driven():
    cfg = _base_config()
    cfg.validators = [{"name": "snapshot", "command": "snapshot-check", "enabled": True, "required": False}]
    adapter = ProjectAdapter(cfg)
    behavior = adapter.translate_to_orchestrator_behavior()

    assert behavior["validators"][0]["name"] == "snapshot"
    selected = validator_runner.select_validators(cfg)
    assert selected[0].name == "snapshot"


def test_run_task_wrapper_delegates_through_live_export_seam(monkeypatch):
    monkeypatch.setattr(
        run_task,
        "_validator_runner_exports",
        lambda: {"run_checks": lambda: (True, "delegated"), "select_validators": None},
    )

    ok, text = run_task.run_checks()
    assert ok is True
    assert text == "delegated"


def test_default_validator_path_preserves_check_runner_behavior(monkeypatch):
    cfg = _base_config()

    monkeypatch.setattr(
        validator_runner.check_runner,
        "run_checks",
        lambda: {"lint_ok": True, "test_ok": False, "output_text": "pytest failed"},
    )

    ok, text = validator_runner.run_checks(cfg)
    assert ok is False
    assert text == "pytest failed"
