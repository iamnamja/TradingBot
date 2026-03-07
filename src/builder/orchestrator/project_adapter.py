from typing import Any, Dict
from .project_config import ProjectConfig, GenericProjectConfig

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
        )
