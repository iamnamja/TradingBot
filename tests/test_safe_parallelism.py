from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

from builder.orchestrator.backlog import BacklogTracker
from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.project_config import ProjectConfig
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.state import OrchestratorState


@dataclass
class ParallelTask:
    order: int
    name: str
    task_class: str
    changed_files: list[str]
    shared_state_keys: list[str]


def _runner(
    *,
    parallel_enabled: bool = False,
    protected: list[str] | None = None,
    approval: list[str] | None = None,
) -> OrchestratorRunner:
    config = ProjectConfig(
        tasks_directory="tasks/",
        lint_command="ruff check .",
        test_command="pytest -q",
        branch_naming_pattern="feature/*",
        protected_file_patterns=protected or [],
        artifact_path_patterns=[],
        approval_required_file_patterns=approval or [],
        validators=[
            {"name": "ruff", "command": "ruff check .", "enabled": True, "required": True},
            {"name": "pytest", "command": "pytest -q", "enabled": True, "required": True},
        ],
        parallel_execution_enabled=parallel_enabled,
    )
    backlog = MagicMock(spec=BacklogTracker)
    return OrchestratorRunner(config, backlog, OrchestratorState(tasks=[]))


def _task(
    order: int,
    name: str,
    task_class: str,
    changed_files: list[str],
    shared_state_keys: list[str] | None = None,
) -> ParallelTask:
    return ParallelTask(
        order=order,
        name=name,
        task_class=task_class,
        changed_files=changed_files,
        shared_state_keys=shared_state_keys or [],
    )


def test_parallelism_defaults_to_serial_mode() -> None:
    runner = _runner(parallel_enabled=False)
    tasks = [
        _task(2, "b", "independent_safe", ["src/b.py"]),
        _task(1, "a", "independent_safe", ["src/a.py"]),
    ]
    groups = runner.build_safe_parallel_groups(tasks)
    assert [[task.order for task in group] for group in groups] == [[1], [2]]


def test_parallel_groups_independent_safe_without_overlap() -> None:
    runner = _runner(parallel_enabled=True)
    tasks = [
        _task(1, "a", "independent_safe", ["src/a.py"]),
        _task(2, "b", "parallel_safe", ["src/b.py"]),
        _task(3, "c", "default", ["src/c.py"]),
    ]
    groups = runner.build_safe_parallel_groups(tasks)
    assert [[task.order for task in group] for group in groups] == [[1, 2], [3]]


def test_parallel_groups_split_on_overlap_and_policy_sensitive_files() -> None:
    runner = _runner(
        parallel_enabled=True,
        protected=[".github/workflows/*"],
        approval=["README.md"],
    )
    tasks = [
        _task(1, "a", "independent_safe", ["src/shared.py"]),
        _task(2, "b", "independent_safe", ["src/shared.py"]),
        _task(3, "c", "independent_safe", ["README.md"]),
        _task(4, "d", "independent_safe", [".github/workflows/ci.yml"]),
    ]
    groups = runner.build_safe_parallel_groups(tasks)
    assert [[task.order for task in group] for group in groups] == [[1], [2], [3], [4]]


def test_parallel_groups_split_on_shared_state_overlap() -> None:
    runner = _runner(parallel_enabled=True)
    tasks = [
        _task(1, "a", "independent_safe", ["src/a.py"], ["cache"]),
        _task(2, "b", "independent_safe", ["src/b.py"], ["cache"]),
        _task(3, "c", "independent_safe", ["src/c.py"], ["index"]),
    ]
    groups = runner.build_safe_parallel_groups(tasks)
    assert [[task.order for task in group] for group in groups] == [[1], [2, 3]]


def test_parallel_fan_in_reporting_is_deterministic() -> None:
    runner = _runner(parallel_enabled=True)
    groups = [[
        _task(2, "b", "independent_safe", []),
        _task(1, "a", "independent_safe", []),
    ]]

    def executor(task: ParallelTask) -> dict[str, int | str]:
        return {"order": task.order, "task_name": task.name}

    results = runner.execute_parallel_groups(groups, executor=executor)
    assert [result["order"] for result in results] == [1, 2]


def test_adapter_translation_exposes_parallel_flag() -> None:
    config = ProjectConfig(
        tasks_directory="tasks/",
        lint_command="ruff check .",
        test_command="pytest -q",
        branch_naming_pattern="feature/*",
        protected_file_patterns=[],
        artifact_path_patterns=[],
        approval_required_file_patterns=[],
        parallel_execution_enabled=True,
    )
    adapter = ProjectAdapter(config)
    behavior = adapter.translate_to_orchestrator_behavior()
    assert behavior["parallel_execution_enabled"] is True


def test_bootstrap_config_defaults_parallel_execution_to_off(tmp_path: Path) -> None:
    from builder.orchestrator.project_config import bootstrap_project_config_scaffold, load_project_config

    config_path = bootstrap_project_config_scaffold(tmp_path)
    loaded = load_project_config(config_path)
    assert loaded.parallel_execution_enabled is False


def test_run_review_contract_for_protected_files_is_shape_stable_and_best_effort() -> None:
    runner = _runner(parallel_enabled=True, protected=[".github/workflows/*"])
    verdict = runner.run_review([".github/workflows/ci.yml"])

    assert set(("mergeable", "reasons", "warnings")).issubset(verdict.keys())
    assert isinstance(verdict["mergeable"], bool)
    assert isinstance(verdict["reasons"], list)
    assert isinstance(verdict["warnings"], list)
