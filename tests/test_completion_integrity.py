from __future__ import annotations

from agents.lib.completion_integrity import (
    DeliverableContract,
    build_completion_repair_feedback,
    evaluate_existing_surface_touch,
    parse_explicit_deliverable_contract,
)


def _task_text() -> str:
    return """# Task 163: orchestrator deliverable contract and completion prompt hardening

Goal

Improve one-task completion quality by making deliverable contracts and completion prompts more explicit, especially for tasks that require wiring into existing live surfaces rather than adding only helper modules.

Why this matters

The first re-proof showed that the orchestrator can still produce partial work that passes local helper tests but does not fully integrate into the live path the task intended to change.

Create or update these exact files
- agents/run_task.py
- agents/lib/completion_integrity.py
- tests/test_completion_integrity.py
- tasks/163_orchestrator_deliverable_contract_and_completion_prompt_hardening.md
- docs/TRADINGBOT_PROJECT_STATE.md

Scope
- Tighten task-text parsing for:
  - exact deliverable contracts
  - required existing-surface touch requirements
  - re-proof / proof task wording
- Improve the prompt feedback appended after a completion-integrity failure so the next iteration is more likely to touch the correct live surface.
- Keep the gate bounded and mechanical. This task is not about scoring quality heuristically; it is about making the contract and repair prompt more explicit.

Acceptance criteria
- Completion-integrity directive parsing supports explicit existing-surface requirements robustly.
- The runner appends clearer feedback when a bundle is rejected for helper-only or new-surface-only completion.
- Tests cover at least one helper-only failure and one existing-surface success case driven by the prompt/contract shape.
- Project state docs note that completion integrity now depends both on the task contract and the follow-up repair prompt.
"""


def test_helper_only_failure_feedback():
    contract: DeliverableContract = parse_explicit_deliverable_contract(_task_text())
    assert "agents/run_task.py" in contract.deliverables
    assert "agents/lib/completion_integrity.py" in contract.deliverables
    # The task explicitly requires touching existing live surfaces
    assert contract.requires_existing_surface is True

    # Helper-only bundle (no required existing-surface files touched)
    bundle_paths = ["helpers/util.py", "new_surface/module.py"]
    existing_repo_paths = {
        "agents/run_task.py",
        "agents/lib/completion_integrity.py",
        "agents/__init__.py",
    }

    evaluation = evaluate_existing_surface_touch(
        contract=contract,
        bundle_paths=bundle_paths,
        existing_repo_paths=existing_repo_paths,
    )
    assert evaluation["status"] == "reject"
    assert evaluation["reason"] == "helper_only"
    assert evaluation["requires_existing_surface"] is True
    assert evaluation["existing_surface_touches"] == []

    feedback = build_completion_repair_feedback(contract, evaluation)
    # Feedback must be explicit and list both required files and what was changed
    assert "COMPLETION-INTEGRITY REPAIR INSTRUCTIONS" in feedback
    assert "- agents/run_task.py" in feedback
    assert "- agents/lib/completion_integrity.py" in feedback
    # Show bundle differences
    assert "- helpers/util.py" in feedback
    assert "- new_surface/module.py" in feedback
    # Include mechanical guidance
    assert "You MUST update these exact existing-surface files" in feedback


def test_existing_surface_success_no_feedback():
    contract: DeliverableContract = parse_explicit_deliverable_contract(_task_text())
    # Bundle touches an existing required surface directly
    bundle_paths = ["agents/run_task.py", "helpers/also_changed.py"]
    existing_repo_paths = {
        "agents/run_task.py",
        "agents/lib/completion_integrity.py",
        "agents/__init__.py",
    }

    evaluation = evaluate_existing_surface_touch(
        contract=contract,
        bundle_paths=bundle_paths,
        existing_repo_paths=existing_repo_paths,
    )
    assert evaluation["status"] == "ok"
    assert evaluation["reason"] == "ok"
    assert evaluation["existing_surface_touches"] == ["agents/run_task.py"]

    feedback = build_completion_repair_feedback(contract, evaluation)
    assert feedback == ""
