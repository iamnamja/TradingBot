from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class ProjectConfig:
    tasks_directory: str
    lint_command: str
    test_command: str
    branch_naming_pattern: str
    protected_file_patterns: List[str]
    artifact_path_patterns: List[str]
    approval_required_file_patterns: List[str]

@dataclass(frozen=True)
class GenericProjectConfig(ProjectConfig):
    pass
