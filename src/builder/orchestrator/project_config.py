from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ProjectConfig:
    tasks_directory: str
    lint_command: str
    test_command: str
    branch_naming_pattern: str
    protected_file_patterns: list[str]
    artifact_path_patterns: list[str]
    approval_required_file_patterns: list[str]
    task_runner_command: str | None = None
    state_path: str | None = None
    task_file_pattern: str = "*.md"
    audit_path: str | None = None
    validators: list[dict[str, Any]] | None = None
    parallel_execution_enabled: bool = False


@dataclass
class GenericProjectConfig(ProjectConfig):
    pass


def build_bootstrap_project_config() -> dict[str, object]:
    cfg = GenericProjectConfig(
        tasks_directory="tasks/",
        lint_command="ruff check .",
        test_command="pytest -q",
        branch_naming_pattern="feature/*",
        protected_file_patterns=[
            "*.pyc",
            "*.log",
            ".env",
        ],
        artifact_path_patterns=[
            "artifacts/*",
            "logs/*",
        ],
        approval_required_file_patterns=[
            "README.md",
            ".github/workflows/*",
        ],
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
    return asdict(cfg)


def bootstrap_project_config_scaffold(target_dir: Path) -> Path:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    config_path = target / "orchestrator_project_config.json"
    payload = build_bootstrap_project_config()
    config_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path


def load_project_config(
    config_path: str | Path = "orchestrator_project_config.json",
) -> ProjectConfig:
    path = Path(config_path)
    if not path.exists():
        data = build_bootstrap_project_config()
        return ProjectConfig(**data)

    data = json.loads(path.read_text(encoding="utf-8"))
    return ProjectConfig(**data)
