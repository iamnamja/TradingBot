from dataclasses import dataclass


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


@dataclass
class GenericProjectConfig(ProjectConfig):
    pass
