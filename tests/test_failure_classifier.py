import importlib
import sys
from pathlib import Path

import pytest
from builder.orchestrator.failures import FailureClassifier

@pytest.fixture
def classifier():
    return FailureClassifier()

def test_classify_missing_deliverables(classifier):
    result = classifier.classify("", "missing required deliverables", [])
    assert result["category"] == "implementation_bug"
    assert result["confidence"] == "High"
    assert result["recommended_action"] == "patch_task"

def test_classify_invented_import(classifier):
    result = classifier.classify("", "invented import/module path", [])
    assert result["category"] == "implementation_bug"
    assert result["confidence"] == "High"
    assert result["recommended_action"] == "patch_task"

def test_classify_ci_dependency_issue(classifier):
    result = classifier.classify("CI missing dependency", "", [])
    assert result["category"] == "ci_dependency_issue"
    assert result["confidence"] == "Medium"
    assert result["recommended_action"] == "patch_ci"

def test_classify_runtime_artifact(classifier):
    result = classifier.classify("runtime artifact committed", "", [])
    assert result["category"] == "repo_hygiene_issue"
    assert result["confidence"] == "Medium"
    assert result["recommended_action"] == "clean_repo"

def test_classify_semantic_mismatch(classifier):
    result = classifier.classify("", "semantic assertion mismatch", [])
    assert result["category"] == "implementation_bug"
    assert result["confidence"] == "High"
    assert result["recommended_action"] == "require_human_review"

def test_classify_unknown(classifier):
    result = classifier.classify("", "some unknown error", [])
    assert result["category"] == "unknown"
    assert result["confidence"] == "Low"
    assert result["recommended_action"] == "require_human_review"


def _load_agent_failure_classifier():
    repo_root = Path(__file__).resolve().parents[1]
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if "agents.lib.failure_classifier" in sys.modules:
        del sys.modules["agents.lib.failure_classifier"]
    return importlib.import_module("agents.lib.failure_classifier")


def test_classify_single_task_failure_import_collection_error():
    module = _load_agent_failure_classifier()
    artifact = module.classify_single_task_failure(
        task_path="tasks/151_orchestrator_external_safe_failure_taxonomy_and_self_heal_router.md",
        required_paths=["tests/test_single_task_runner.py"],
        execution_summary={
            "stdout_tail": "E   ModuleNotFoundError: No module named 'agents.lib.missing'\nFAILED tests/test_single_task_runner.py::test_demo",
            "stderr_tail": "",
        },
        verifier_artifact={
            "verdict": "fail",
            "lint_ok": True,
            "test_ok": False,
            "likely_failure_family": "import_contract",
            "tester_critique_bundle": {
                "failing_test_files": ["tests/test_single_task_runner.py"],
                "focused_replay_commands": ["pytest -q tests/test_single_task_runner.py"],
                "broad_replay_commands": ["py -m pytest -q"],
            },
        },
    )

    assert artifact["failure_family"] == "import_collection_error"
    assert artifact["self_heal_lane"] == "focused_import_collection_repair"
    assert artifact["confidence"] == "high"
    assert artifact["evidence_paths"] == ["tests/test_single_task_runner.py"]


def test_classify_single_task_failure_detects_incomplete_deliverable_coverage():
    module = _load_agent_failure_classifier()
    artifact = module.classify_single_task_failure(
        task_path="tasks/151_orchestrator_external_safe_failure_taxonomy_and_self_heal_router.md",
        required_paths=["agents/lib/failure_classifier.py", "agents/lib/repair_planner.py"],
        execution_summary={
            "stdout_tail": "missing required deliverables: agents/lib/repair_planner.py",
            "stderr_tail": "",
            "missing_deliverable_retry_observed": True,
        },
        verifier_artifact={
            "verdict": "fail",
            "lint_ok": False,
            "test_ok": False,
            "tester_critique_bundle": {
                "focused_replay_commands": ["pytest -q tests/test_single_task_runner.py"],
            },
        },
    )

    assert artifact["failure_family"] == "incomplete_deliverable_coverage"
    assert artifact["self_heal_lane"] == "deliverable_patch_only"
    assert artifact["matched_signals"] == ["missing_deliverable_signal"]
    assert artifact["evidence_paths"] == ["agents/lib/failure_classifier.py", "agents/lib/repair_planner.py"]


def test_classify_single_task_failure_detects_lint_only_failures():
    module = _load_agent_failure_classifier()
    artifact = module.classify_single_task_failure(
        task_path="tasks/151_orchestrator_external_safe_failure_taxonomy_and_self_heal_router.md",
        required_paths=["agents/lib/failure_classifier.py"],
        execution_summary={
            "stdout_tail": "ruff failed\nE402 Module level import not at top of file",
            "stderr_tail": "",
        },
        verifier_artifact={
            "verdict": "fail",
            "lint_ok": False,
            "test_ok": True,
            "tester_critique_bundle": {
                "focused_replay_commands": ["ruff check agents/lib/failure_classifier.py"],
                "broad_replay_commands": ["ruff check .", "py -m pytest -q"],
            },
        },
    )

    assert artifact["failure_family"] == "formatting_lint_only"
    assert artifact["self_heal_lane"] == "lint_only_repair"
    assert artifact["confidence"] == "high"
