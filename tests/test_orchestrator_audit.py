import os
import tempfile
import pytest
from builder.orchestrator.audit import (
    log_selected_task,
    log_classification_result,
    log_review_verdict,
    log_pr_action,
    log_merge_decision,
    log_repair_decision,
    log_stop_escalation_decision,
)

@pytest.fixture
def temp_audit_file():
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        yield tmp_file.name
    os.remove(tmp_file.name)

def test_log_selected_task(temp_audit_file):
    log_selected_task("test_task", audit_path=temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        content = f.readlines()
    assert len(content) == 1
    assert "selected_task" in content[0]

def test_log_classification_result(temp_audit_file):
    log_classification_result("positive", audit_path=temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        content = f.readlines()
    assert len(content) == 1
    assert "classification_result" in content[0]

def test_log_review_verdict(temp_audit_file):
    log_review_verdict("approved", audit_path=temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        content = f.readlines()
    assert len(content) == 1
    assert "review_verdict" in content[0]

def test_log_pr_action(temp_audit_file):
    log_pr_action("create", audit_path=temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        content = f.readlines()
    assert len(content) == 1
    assert "pr_action" in content[0]

def test_log_merge_decision(temp_audit_file):
    log_merge_decision("merge", audit_path=temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        content = f.readlines()
    assert len(content) == 1
    assert "merge_decision" in content[0]

def test_log_repair_decision(temp_audit_file):
    log_repair_decision("repair", audit_path=temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        content = f.readlines()
    assert len(content) == 1
    assert "repair_decision" in content[0]

def test_log_stop_escalation_decision(temp_audit_file):
    log_stop_escalation_decision("stop", audit_path=temp_audit_file)
    with open(temp_audit_file, 'r') as f:
        content = f.readlines()
    assert len(content) == 1
    assert "stop_escalation_decision" in content[0]
