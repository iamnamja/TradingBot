from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .project_config import GenericProjectConfig, ProjectConfig


class ProjectAdapter:
    def __init__(self, config: ProjectConfig):
        self.config = config

    def translate_to_orchestrator_behavior(self) -> Dict[str, Any]:
        return {
            "tasks_directory": self.config.tasks_directory,
            "lint_command": self.config.lint_command,
            "test_command": self.config.test_command,
            "branch_naming_pattern": self.config.branch_naming_pattern,
            "protected_file_patterns": self.config.protected_file_patterns,
            "artifact_path_patterns": self.config.artifact_path_patterns,
            "approval_required_file_patterns": self.config.approval_required_file_patterns,
            "task_runner_command": getattr(self.config, "task_runner_command", None),
            "state_path": getattr(self.config, "state_path", None),
            "task_file_pattern": getattr(self.config, "task_file_pattern", "*.md"),
            "audit_path": getattr(self.config, "audit_path", None),
            "validators": getattr(self.config, "validators", None),
            "parallel_execution_enabled": getattr(
                self.config, "parallel_execution_enabled", False
            ),
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
                {"name": "lint", "command": "flake8 .", "enabled": True, "required": True},
                {
                    "name": "tests",
                    "command": "pytest tests/test_generic.py",
                    "enabled": True,
                    "required": True,
                },
            ],
            parallel_execution_enabled=False,
        )


def build_bootstrap_starter_docs_text() -> str:
    return (
        "# Orchestrator Starter Notes\n\n"
        "This scaffold is intentionally generic and reusable for new repositories.\n\n"
        "## Where tasks live\n"
        "- Put markdown tasks under `tasks/`.\n\n"
        "## Task template reference\n"
        "Use `tasks/task_template.md` for new tasks.\n"
        "An example task is also provided at `tasks/001_example_task.md`.\n\n"
        "## Parallel execution\n"
        "- Keep `parallel_execution_enabled` false unless a project explicitly opts in.\n"
        "- Only tasks marked `task_class: independent_safe` may be considered for parallel grouping.\n"
    )


def build_bootstrap_task_template_text() -> str:
    return (
        "# Task NNN — Title\n\n"
        "## Goal\n"
        "Describe what should be implemented.\n\n"
        "## Deliverables\n"
        "- `src/...`\n"
        "- `tests/...`\n\n"
        "## Acceptance criteria\n"
        "- `ruff check .` passes\n"
        "- `pytest -q` passes\n\n"
        "## Safety\n"
        "- `task_class: default` unless the task is explicitly independent and safe\n"
        "- use `task_class: independent_safe` only when there is no shared mutable state\n"
        "  and no overlap with protected or approval-sensitive files\n"
    )


def build_bootstrap_adapter_stub_text() -> str:
    return (
        "from builder.orchestrator.project_adapter import ProjectAdapter\n"
        "from builder.orchestrator.project_config import ProjectConfig\n\n\n"
        "def build_project_adapter() -> ProjectAdapter:\n"
        "    config = ProjectConfig(\n"
        "        tasks_directory=\"tasks/\",\n"
        "        lint_command=\"ruff check .\",\n"
        "        test_command=\"pytest -q\",\n"
        "        branch_naming_pattern=\"feature/*\",\n"
        "        protected_file_patterns=[\"*.pyc\", \"*.log\"],\n"
        "        artifact_path_patterns=[\"artifacts/*\"],\n"
        "        approval_required_file_patterns=[\"README.md\"],\n"
        "        task_runner_command=None,\n"
        "        state_path=\"tasks/state.json\",\n"
        "        task_file_pattern=\"*.md\",\n"
        "        audit_path=\"logs/orchestrator_audit.jsonl\",\n"
        "        validators=[\n"
        "            {\"name\": \"ruff\", \"command\": \"ruff check .\", \"enabled\": True, \"required\": True},\n"
        "            {\"name\": \"pytest\", \"command\": \"pytest -q\", \"enabled\": True, \"required\": True},\n"
        "        ],\n"
        "        parallel_execution_enabled=False,\n"
        "    )\n"
        "    return ProjectAdapter(config)\n"
    )


def bootstrap_project_adapter_scaffold(target_dir: Path) -> dict[str, Path]:
    target = Path(target_dir)
    tasks_dir = target / "tasks"
    docs_dir = target / "docs"
    adapter_dir = target / "src" / "builder" / "orchestrator"

    tasks_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    adapter_dir.mkdir(parents=True, exist_ok=True)

    template_path = tasks_dir / "task_template.md"
    example_path = tasks_dir / "001_example_task.md"
    docs_path = docs_dir / "orchestrator_starter.md"
    adapter_stub_path = adapter_dir / "project_adapter_factory.py"
    validator_path = target / ".orchestrator_validator.json"

    template_text = build_bootstrap_task_template_text()
    template_path.write_text(template_text, encoding="utf-8")
    example_path.write_text(
        template_text.replace("NNN", "001").replace("Title", "Example"),
        encoding="utf-8",
    )
    docs_path.write_text(build_bootstrap_starter_docs_text(), encoding="utf-8")
    adapter_stub_path.write_text(build_bootstrap_adapter_stub_text(), encoding="utf-8")
    validator_path.write_text(
        "{\n"
        "  \"required_tools\": [\"ruff\", \"pytest\"],\n"
        "  \"required_commands\": [\"ruff check .\", \"pytest -q\"]\n"
        "}\n",
        encoding="utf-8",
    )

    return {
        "docs": docs_path,
        "task_template": template_path,
        "task_example": example_path,
        "adapter_factory": adapter_stub_path,
        "validator_config": validator_path,
    }
