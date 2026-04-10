from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _bootstrap_repo_root() -> None:
    root = str(_repo_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def _load_safe_lint_preflight_module():
    _bootstrap_repo_root()
    if "agents.lib.safe_lint_preflight" in sys.modules:
        del sys.modules["agents.lib.safe_lint_preflight"]
    return importlib.import_module("agents.lib.safe_lint_preflight")


def test_build_safe_lint_preflight_plan_only_allows_lint_only_python_paths() -> None:
    module = _load_safe_lint_preflight_module()

    plan = module.build_safe_lint_preflight_plan(
        task_path="tasks/155_orchestrator_safe_lint_preflight_normalization.md",
        required_paths=["tests/test_single_task_runner.py", "docs/TRADINGBOT_PROJECT_STATE.md"],
        verifier_artifact={
            "focused_validation_commands": ["ruff check tests/test_single_task_runner.py"],
            "full_validation_commands": ["ruff check .", "py -m pytest -q"],
        },
        failure_taxonomy={"failure_family": "formatting_lint_only"},
    )

    assert plan["attempt_allowed"] is True
    assert plan["python_paths"] == ["tests/test_single_task_runner.py"]
    assert plan["normalization_commands"][0][:3] == ["ruff", "check", "--fix"]
    assert plan["broad_validation_commands"] == [["py", "-m", "pytest", "-q"]]


def test_run_safe_lint_preflight_succeeds_after_fix_and_replay() -> None:
    module = _load_safe_lint_preflight_module()
    calls: list[list[str]] = []

    def fake_executor(command):
        calls.append(list(command))
        if command[:3] == ["ruff", "check", "--fix"]:
            return {"command": list(command), "returncode": 0, "stdout": "fixed", "stderr": ""}
        if command[:2] == ["ruff", "format"]:
            return {"command": list(command), "returncode": 0, "stdout": "formatted", "stderr": ""}
        if command[:2] == ["ruff", "check"]:
            return {"command": list(command), "returncode": 0, "stdout": "All checks passed!", "stderr": ""}
        if command[:4] == ["py", "-m", "pytest", "-q"]:
            return {"command": list(command), "returncode": 0, "stdout": "[100%]", "stderr": ""}
        raise AssertionError(f"Unexpected command: {command}")

    plan = module.build_safe_lint_preflight_plan(
        task_path="tasks/155_orchestrator_safe_lint_preflight_normalization.md",
        required_paths=["tests/test_single_task_runner.py"],
        verifier_artifact={
            "focused_validation_commands": ["ruff check tests/test_single_task_runner.py"],
            "full_validation_commands": ["ruff check .", "py -m pytest -q"],
        },
        failure_taxonomy={"failure_family": "formatting_lint_only"},
    )
    artifact = module.run_safe_lint_preflight(plan, executor=fake_executor)

    assert artifact["attempted"] is True
    assert artifact["succeeded"] is True
    assert artifact["lint_green_after_normalization"] is True
    assert artifact["broad_validation_green_after_normalization"] is True
    assert calls[0][:3] == ["ruff", "check", "--fix"]


def test_apply_safe_lint_preflight_execution_summary_marks_green_completion() -> None:
    module = _load_safe_lint_preflight_module()

    updated = module.apply_safe_lint_preflight_execution_summary(
        {
            "returncode": 1,
            "ruff_green_observed": False,
            "pytest_green_observed": False,
            "all_checks_passed_observed": False,
            "stdout_tail": "ruff failed",
        },
        {
            "attempted": True,
            "succeeded": True,
            "reason": "lint only",
            "python_paths": ["tests/test_single_task_runner.py"],
            "lint_green_after_normalization": True,
            "broad_validation_green_after_normalization": True,
            "normalization_results": [{"stdout": "fixed", "stderr": ""}],
            "lint_replay_results": [{"stdout": "All checks passed!", "stderr": ""}],
            "broad_validation_results": [{"stdout": "[100%]", "stderr": ""}],
        },
    )

    assert updated["returncode"] == 0
    assert updated["safe_lint_preflight_attempted"] is True
    assert updated["safe_lint_preflight_succeeded"] is True
    assert updated["ruff_green_observed"] is True
    assert updated["pytest_green_observed"] is True
    assert updated["all_checks_passed_observed"] is True
