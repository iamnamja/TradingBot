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
