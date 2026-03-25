from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .project_config import GenericProjectConfig, ProjectConfig, load_project_config


class ProjectAdapter:
    def __init__(self, config: ProjectConfig):
        self.config = config

    def translate_to_orchestrator_behavior(self) -> dict[str, Any]:
        return {
            "tasks_directory": self.config.tasks_directory,
            "lint_command": self.config.lint_command,
            "test_command": self.config.test_command,
            "branch_naming_pattern": self.config.branch_naming_pattern,
            "protected_file_patterns": list(self.config.protected_file_patterns),
            "artifact_path_patterns": list(self.config.artifact_path_patterns),
            "approval_required_file_patterns": list(self.config.approval_required_file_patterns),
            "task_runner_command": self.config.task_runner_command,
            "state_path": self.config.state_path,
            "task_file_pattern": self.config.task_file_pattern,
            "audit_path": self.config.audit_path,
            "validators": self.config.validators,
            "parallel_execution_enabled": self.config.parallel_execution_enabled,
        }

    @staticmethod
    def get_tradingbot_default_config() -> ProjectConfig:
        return ProjectConfig(
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
            validators=[
                {"name": "ruff", "command": "ruff check .", "enabled": True, "required": True},
                {"name": "pytest", "command": "pytest -q", "enabled": True, "required": True},
            ],
            parallel_execution_enabled=False,
        )

    @staticmethod
    def get_generic_project_config() -> GenericProjectConfig:
        return GenericProjectConfig(
            tasks_directory="generic_tasks/",
            lint_command="flake8 .",
            test_command="pytest tests/test_generic.py",
            branch_naming_pattern="feature/generic/*",
            protected_file_patterns=["*.tmp"],
            artifact_path_patterns=["generic_artifacts/*"],
            approval_required_file_patterns=["README.md"],
            task_runner_command=None,
            state_path=None,
            task_file_pattern="*.task.md",
            audit_path=None,
            validators=[
                {"name": "flake8", "command": "flake8 .", "enabled": True, "required": True},
                {"name": "pytest", "command": "pytest tests/test_generic.py", "enabled": True, "required": True},
            ],
            parallel_execution_enabled=False,
        )


def build_bootstrap_starter_docs_text() -> str:
    return (
        "# Project Orchestrator Bootstrap\n\n"
        "This repository is configured for orchestrator-driven task execution as a generic and reusable setup.\n"
        "Create tasks in `tasks/` such as `tasks/001_example_task.md`, copy from `tasks/task_template.md`, "
        "and tune behavior in `orchestrator_project_config.json`.\n"
    )


def build_bootstrap_task_template_text() -> str:
    return (
        "# Task Template\n\n"
        "## Goal\n"
        "Describe the desired outcome.\n\n"
        "## Deliverables\n"
        "- Updated source files\n"
        "- Tests and/or docs as needed\n\n"
        "## Checks\n"
        "- ruff check .\n"
        "- pytest -q\n"
    )


def bootstrap_project_adapter_scaffold(repo_root: str | Path) -> dict[str, Path]:
    root = Path(repo_root)
    docs_dir = root / "docs"
    tasks_dir = root / "tasks"
    src_dir = root / "src" / "builder" / "orchestrator"

    docs_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)

    docs_path = docs_dir / "orchestrator_starter.md"
    task_template_path = tasks_dir / "task_template.md"
    task_example_path = tasks_dir / "001_example_task.md"
    adapter_factory_path = src_dir / "project_adapter_factory.py"
    validator_config_path = root / ".orchestrator_validator.json"

    docs_path.write_text(build_bootstrap_starter_docs_text(), encoding="utf-8")
    task_template_path.write_text(build_bootstrap_task_template_text(), encoding="utf-8")
    if not task_example_path.exists():
        task_example_path.write_text(
            "# Task 001 — Example task\n\n## Goal\n\nProvide a concrete starting point.\n",
            encoding="utf-8",
        )
    adapter_factory_path.write_text(
        "from builder.orchestrator.project_adapter import load_project_adapter\n",
        encoding="utf-8",
    )
    validator_config_path.write_text(json.dumps({"validators": []}, indent=2) + "\n", encoding="utf-8")

    return {
        "docs": docs_path,
        "task_template": task_template_path,
        "task_example": task_example_path,
        "adapter_factory": adapter_factory_path,
        "validator_config": validator_config_path,
    }


def load_project_adapter(path_or_root: str | Path) -> ProjectAdapter:
    path = Path(path_or_root)
    config_path = path / "project_config.json" if path.is_dir() else path
    return ProjectAdapter(load_project_config(config_path))
