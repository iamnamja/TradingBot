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
