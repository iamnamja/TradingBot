from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    for candidate in (str(root), str(src)):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def test_public_surface_ownership_and_shell_exports() -> None:
    _ensure_repo_on_path()
    cfg_module = importlib.import_module("builder.orchestrator.project_config")
    adapter_module = importlib.import_module("builder.orchestrator.project_adapter")
    run_task = importlib.import_module("agents.run_task")

    assert hasattr(cfg_module, "bootstrap_project_config_scaffold")
    assert hasattr(adapter_module, "bootstrap_project_adapter_scaffold")
    assert hasattr(adapter_module, "build_bootstrap_starter_docs_text")
    assert hasattr(adapter_module, "build_bootstrap_task_template_text")

    exports = run_task._bootstrap_exports()
    assert list(exports) == [
        "bootstrap_project_config_scaffold",
        "bootstrap_project_adapter_scaffold",
    ]
    assert callable(exports["bootstrap_project_config_scaffold"])
    assert callable(exports["bootstrap_project_adapter_scaffold"])


def test_generic_default_config_compatibility_freeze() -> None:
    _ensure_repo_on_path()
    from builder.orchestrator.project_adapter import ProjectAdapter

    cfg = ProjectAdapter.get_generic_project_config()
    assert cfg.state_path is None
    assert cfg.audit_path is None
    assert cfg.task_file_pattern == "*.task.md"
    assert cfg.artifact_path_patterns == ["generic_artifacts/*"]
    assert cfg.approval_required_file_patterns == ["README.md"]


def test_validator_default_path_is_legacy_non_plugin(monkeypatch) -> None:
    _ensure_repo_on_path()
    validator_runner = importlib.import_module("agents.lib.validator_runner")

    called = {"plugin": False}

    def _boom(*args, **kwargs):
        called["plugin"] = True
        raise AssertionError("plugin path must not run for config=None")

    monkeypatch.setattr(validator_runner, "run_validator", _boom)
    monkeypatch.setattr(
        validator_runner.check_runner,
        "run_checks",
        lambda: {"lint_ok": True, "test_ok": False, "output_text": "pytest failed"},
    )

    ok, output = validator_runner.run_checks(config=None)

    assert ok is False
    assert output == "pytest failed"
    assert called["plugin"] is False
