import importlib
import sys
from pathlib import Path

from builder.orchestrator.repair import RepairWorkflow

def test_determine_repair_action_runner_weakness():
    workflow = RepairWorkflow(failure_classification=["runner_weakness"], changed_files=[])
    result = workflow.determine_repair_action()
    assert result == {
        "action": "patch_runner",
        "requires_approval": True,
        "reason": "Runner weakness detected."
    }

def test_determine_repair_action_ci_dependency_issue():
    workflow = RepairWorkflow(failure_classification=["ci_dependency_issue"], changed_files=[])
    result = workflow.determine_repair_action()
    assert result == {
        "action": "patch_ci",
        "requires_approval": True,
        "reason": "CI dependency issue detected."
    }

def test_determine_repair_action_repo_hygiene_issue():
    workflow = RepairWorkflow(failure_classification=["repo_hygiene_issue"], changed_files=[])
    result = workflow.determine_repair_action()
    assert result == {
        "action": "clean_repo",
        "requires_approval": False,
        "reason": "Repository hygiene issue detected."
    }

def test_determine_repair_action_task_ambiguity():
    workflow = RepairWorkflow(failure_classification=["task_ambiguity"], changed_files=[])
    result = workflow.determine_repair_action()
    assert result == {
        "action": "require_human_review",
        "requires_approval": True,
        "reason": "Task ambiguity requires human review."
    }

def test_determine_repair_action_unknown_failure():
    workflow = RepairWorkflow(failure_classification=["unknown"], changed_files=[])
    result = workflow.determine_repair_action()
    assert result == {
        "action": "require_human_review",
        "requires_approval": True,
        "reason": "Unknown failure requires human review."
    }


def _load_single_task_repair_loop():
    repo_root = Path(__file__).resolve().parents[1]
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if "agents.lib.repair_loop" in sys.modules:
        del sys.modules["agents.lib.repair_loop"]
    return importlib.import_module("agents.lib.repair_loop")


def test_select_single_task_targeted_repair_prefers_focused_replay() -> None:
    repair_loop = _load_single_task_repair_loop()

    artifact = repair_loop.select_single_task_targeted_repair(
        task_path="tasks/150_orchestrator_one_task_multi_agent_dev_test_repair_loop.md",
        developer_artifact={"retry_count_observed": 0},
        verifier_artifact={
            "verdict": "fail",
            "focused_results": ["pytest -q tests/test_single_task_runner.py"],
            "full_results": ["pytest -q"],
            "tester_critique_bundle": {
                "likely_failure_family": "import_contract",
                "focused_replay_commands": ["pytest -q tests/test_single_task_runner.py"],
                "broad_replay_commands": ["pytest -q"],
            },
        },
        max_repair_attempts_within_run=1,
    )

    assert artifact["repair_required"] is True
    assert artifact["repair_attempt_selected"] is True
    assert artifact["repair_budget_remaining"] == 1
    assert artifact["repair_strategy"] == "focused_replay_then_targeted_patch"
    assert artifact["next_role"] == "builder"
    assert artifact["escalation_required"] is False


def test_select_single_task_targeted_repair_escalates_when_budget_is_exhausted() -> None:
    repair_loop = _load_single_task_repair_loop()

    artifact = repair_loop.select_single_task_targeted_repair(
        task_path="tasks/150_orchestrator_one_task_multi_agent_dev_test_repair_loop.md",
        developer_artifact={"retry_count_observed": 1},
        verifier_artifact={
            "verdict": "fail",
            "focused_results": ["pytest -q tests/test_single_task_runner.py"],
            "tester_critique_bundle": {
                "likely_failure_family": "import_contract",
                "focused_replay_commands": ["pytest -q tests/test_single_task_runner.py"],
            },
        },
        max_repair_attempts_within_run=1,
    )

    assert artifact["repair_required"] is True
    assert artifact["repair_attempt_selected"] is False
    assert artifact["repair_budget_exhausted"] is True
    assert artifact["repair_strategy"] == "supervised_escalation"
    assert artifact["next_role"] == "operator"
    assert artifact["escalation_required"] is True
