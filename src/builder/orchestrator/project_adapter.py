from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, TypedDict

from .project_config import GenericProjectConfig, ProjectConfig


class ProjectBehavior(TypedDict):
    tasks_directory: str
    lint_command: str
    test_command: str
    branch_naming_pattern: str
    protected_file_patterns: list[str]
    artifact_path_patterns: list[str]
    approval_required_file_patterns: list[str]
    task_runner_command: str | None
    state_path: str | None
    task_file_pattern: str
    audit_path: str | None
    validators: list[dict[str, Any]] | None
    parallel_execution_enabled: bool


class ProjectAdapterTranslation(Protocol):
    def translate_to_orchestrator_behavior(self) -> ProjectBehavior: ...


class ProjectAdapter:
    def __init__(self, config: ProjectConfig):
        self.config = config

    def translate_to_orchestrator_behavior(self) -> ProjectBehavior:
        return {
            "tasks_directory": self.config.tasks_directory,
            "lint_command": self.config.lint_command,
            "test_command": self.config.test_command,
            "branch_naming_pattern": self.config.branch_naming_pattern,
            "protected_file_patterns": self.config.protected_file_patterns,
            "artifact_path_patterns": self.config.artifact_path_patterns,
            "approval_required_file_patterns": self.config.approval_required_file_patterns,
            "task_runner_command": self.config.task_runner_command,
            "state_path": self.config.state_path,
            "task_file_pattern": self.config.task_file_pattern,
            "audit_path": self.config.audit_path,
            "validators": self.config.validators,
            "parallel_execution_enabled": self.config.parallel_execution_enabled,
        }

    def export_public_behavior(self) -> ProjectBehavior:
        return self.translate_to_orchestrator_behavior()

    @staticmethod
    def get_tradingbot_default_config() -> ProjectConfig:
        return ProjectConfig(
            tasks_directory="tasks/",
            lint_command="ruff check .",
            test_command="pytest -q",
            branch_naming_pattern="feature/*",
            protected_file_patterns=["*.pyc", "*.log", ".env"],
            artifact_path_patterns=["artifacts/*", "logs/*"],
            approval_required_file_patterns=["README.md", ".github/workflows/*"],
            task_runner_command=None,
            state_path="tasks/state.json",
            task_file_pattern="*.md",
            audit_path="logs/orchestrator_audit.jsonl",
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
            validators=None,
            parallel_execution_enabled=False,
        )


def build_bootstrap_starter_docs_text() -> str:
    return (
        "# Orchestrator Starter Docs\n\n"
        "This scaffold is generic and reusable.\n\n"
        "Start with tasks/001_example_task.md and use task_template.md as the starting template for new tasks.\n"
    )


def build_bootstrap_task_template_text() -> str:
    return (
        "# Task Template\n\n"
        "## Goal\n"
        "Describe the exact change and success criteria.\n\n"
        "## Deliverables\n"
        "- Updated source files\n"
        "- Tests and/or docs as needed\n\n"
        "## Checks\n"
        "- ruff check .\n"
        "- pytest -q\n"
    )


def bootstrap_project_adapter_scaffold(target_dir: str | Path) -> dict[str, Path]:
    root = Path(target_dir)
    docs_dir = root / "docs"
    tasks_dir = root / "tasks"
    adapter_src_dir = root / "src" / "builder" / "orchestrator"

    docs_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir.mkdir(parents=True, exist_ok=True)
    adapter_src_dir.mkdir(parents=True, exist_ok=True)

    docs_path = docs_dir / "orchestrator_starter.md"
    task_template_path = tasks_dir / "task_template.md"
    task_example_path = tasks_dir / "001_example_task.md"
    adapter_factory_path = adapter_src_dir / "project_adapter_factory.py"
    validator_config_path = root / ".orchestrator_validator.json"

    docs_path.write_text(build_bootstrap_starter_docs_text(), encoding="utf-8", newline="\n")
    task_template_path.write_text(build_bootstrap_task_template_text(), encoding="utf-8", newline="\n")
    task_example_path.write_text(
        "# Example Task\n\n## Goal\nCreate a small generic and reusable change.\n",
        encoding="utf-8",
        newline="\n",
    )
    adapter_factory_path.write_text(
        "from builder.orchestrator.project_adapter import ProjectAdapter\n",
        encoding="utf-8",
        newline="\n",
    )
    validator_config_path.write_text(
        json.dumps({"validators": []}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return {
        "docs": docs_path,
        "task_template": task_template_path,
        "task_example": task_example_path,
        "adapter_factory": adapter_factory_path,
        "validator_config": validator_config_path,
    }


def build_bootstrap_project_adapter(target_dir: str | Path) -> dict[str, Path]:
    return bootstrap_project_adapter_scaffold(target_dir)
