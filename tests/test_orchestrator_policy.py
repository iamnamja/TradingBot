import pytest
from builder.orchestrator.policy import PolicyEngine

@pytest.fixture
def policy_engine():
    return PolicyEngine(
        protected_file_patterns=["protected_file.py"],
        approval_required_file_patterns=["README.md", "CHANGELOG.md"]
    )

def test_blocked_due_to_protected_file(policy_engine):
    result = policy_engine.evaluate(changed_files=["protected_file.py"], failure_category="", requested_action="")
    assert result["decision"] == "blocked"
    assert result["reason"] == "Protected file modification."

def test_requires_approval_for_workflow_change(policy_engine):
    result = policy_engine.evaluate(changed_files=[], failure_category="workflow_ci_changes", requested_action="")
    assert result["decision"] == "requires_approval"
    assert result["reason"] == "Approval required for this action."

def test_requires_approval_for_dependency_change(policy_engine):
    result = policy_engine.evaluate(changed_files=[], failure_category="dependency_management_changes", requested_action="")
    assert result["decision"] == "requires_approval"
    assert result["reason"] == "Approval required for this action."

def test_requires_approval_for_live_trading_change(policy_engine):
    result = policy_engine.evaluate(changed_files=[], failure_category="live_trading_safety_changes", requested_action="")
    assert result["decision"] == "requires_approval"
    assert result["reason"] == "Approval required for this action."

def test_allowed_action(policy_engine):
    result = policy_engine.evaluate(changed_files=[], failure_category="", requested_action="")
    assert result["decision"] == "allowed"
    assert result["reason"] == "Action allowed."

def test_requires_approval_for_requested_action(policy_engine):
    result = policy_engine.evaluate(changed_files=[], failure_category="", requested_action="README.md")
    assert result["decision"] == "requires_approval"
    assert result["reason"] == "Approval required for this action."
