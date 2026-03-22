from __future__ import annotations

import json
from pathlib import Path

from builder.orchestrator.project_adapter import (
    bootstrap_project_adapter_scaffold,
    build_bootstrap_starter_docs_text,
    build_bootstrap_task_template_text,
)
from builder.orchestrator.project_config import bootstrap_project_config_scaffold


def test_bootstrap_creates_expected_scaffold_deterministically(tmp_path: Path) -> None:
    cfg_path = bootstrap_project_config_scaffold(tmp_path)
    generated = bootstrap_project_adapter_scaffold(tmp_path)

    assert cfg_path == tmp_path / "orchestrator_project_config.json"
    assert generated["docs"] == tmp_path / "docs" / "orchestrator_starter.md"
    assert generated["task_template"] == tmp_path / "tasks" / "task_template.md"
    assert generated["task_example"] == tmp_path / "tasks" / "001_example_task.md"
    assert generated["adapter_factory"] == tmp_path / "src" / "builder" / "orchestrator" / "project_adapter_factory.py"
    assert generated["validator_config"] == tmp_path / ".orchestrator_validator.json"

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg["tasks_directory"] == "tasks/"
    assert cfg["lint_command"] == "ruff check ."
    assert cfg["test_command"] == "pytest -q"


def test_generated_scaffold_is_generic_reusable_starting_point(tmp_path: Path) -> None:
    bootstrap_project_config_scaffold(tmp_path)
    bootstrap_project_adapter_scaffold(tmp_path)

    docs_text = (tmp_path / "docs" / "orchestrator_starter.md").read_text(encoding="utf-8")
    cfg_text = (tmp_path / "orchestrator_project_config.json").read_text(encoding="utf-8")
    tmpl_text = (tmp_path / "tasks" / "task_template.md").read_text(encoding="utf-8")

    assert "TradingBot" not in docs_text
    assert "TradingBot" not in cfg_text
    assert "TradingBot" not in tmpl_text
    assert "generic and reusable" in docs_text


def test_starter_docs_and_template_references_present() -> None:
    docs = build_bootstrap_starter_docs_text()
    template = build_bootstrap_task_template_text()

    assert "tasks/001_example_task.md" in docs
    assert "task_template.md" in docs
    assert "## Deliverables" in template
    assert "ruff check ." in template


def test_bootstrap_logic_lives_outside_run_task_shell() -> None:
    run_task_text = Path("agents/run_task.py").read_text(encoding="utf-8")
    assert "build_bootstrap_starter_docs_text" not in run_task_text
    assert "build_bootstrap_task_template_text" not in run_task_text
    assert "bootstrap_project_adapter_scaffold" in run_task_text
    assert "bootstrap_project_config_scaffold" in run_task_text


def test_run_task_shell_bootstrap_surface_is_additive() -> None:
    run_task_text = Path("agents/run_task.py").read_text(encoding="utf-8")
    assert 'ap.add_argument("task", nargs="?"' in run_task_text
    assert '--bootstrap-project' in run_task_text
    assert "Task file path is required unless --bootstrap-project is used." in run_task_text
