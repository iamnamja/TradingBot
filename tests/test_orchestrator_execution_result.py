"""
Tests for execution result normalization layer.
"""

from builder.orchestrator.execution_result import normalize_execution_result


def test_normalize_success_case():
    raw = {
        "success": True,
        "returncode": 0,
        "stdout": "All tests passed",
        "stderr": "",
        "changed_files": ["src/module.py", "tests/test_module.py"],
    }

    result = normalize_execution_result(raw)

    assert result["success"] is True
    assert result["status"] == "success"
    assert result["output"] == "All tests passed"
    assert result["failure_text"] == ""
    assert result["changed_files"] == ["src/module.py", "tests/test_module.py"]
    assert result["deliverables_updated"] == []
    assert result["raw_stdout"] == "All tests passed"
    assert result["raw_stderr"] == ""
    assert result["returncode"] == 0


def test_normalize_lint_failure():
    raw = {
        "success": False,
        "returncode": 1,
        "stdout": "",
        "stderr": "src/module.py:10: E501 line too long",
    }

    result = normalize_execution_result(raw)

    assert result["success"] is False
    assert result["status"] == "failure"
    assert result["output"] == "src/module.py:10: E501 line too long"
    assert result["failure_text"] == "src/module.py:10: E501 line too long"
    assert result["changed_files"] == []
    assert result["returncode"] == 1


def test_normalize_test_failure():
    raw = {
        "success": False,
        "returncode": 1,
        "stdout": "FAILED tests/test_module.py::test_function - AssertionError",
        "stderr": "",
    }

    result = normalize_execution_result(raw)

    assert result["success"] is False
    assert result["status"] == "failure"
    assert "AssertionError" in result["failure_text"]
    assert result["returncode"] == 1


def test_normalize_missing_deliverables():
    raw = {
        "success": False,
        "returncode": 1,
        "stdout": "Error: missing required deliverables",
        "stderr": "",
    }

    result = normalize_execution_result(raw)

    assert result["success"] is False
    assert result["status"] == "failure"
    assert "missing" in result["failure_text"].lower()
    assert "deliverable" in result["failure_text"].lower()


def test_normalize_malformed_input():
    raw = {}

    result = normalize_execution_result(raw)

    assert result["success"] is True
    assert result["status"] == "success"
    assert result["output"] == "No output"
    assert result["failure_text"] == ""
    assert result["changed_files"] == []
    assert result["returncode"] == 0


def test_normalize_unknown_failure():
    raw = {
        "success": False,
        "returncode": 137,
        "stdout": "",
        "stderr": "Segmentation fault",
    }

    result = normalize_execution_result(raw)

    assert result["success"] is False
    assert result["status"] == "failure"
    assert result["failure_text"] == "Segmentation fault"
    assert result["returncode"] == 137


def test_normalize_combined_stdout_stderr():
    raw = {
        "success": False,
        "returncode": 1,
        "stdout": "Running tests...",
        "stderr": "Error: test failed",
    }

    result = normalize_execution_result(raw)

    assert result["success"] is False
    assert "Running tests..." in result["output"]
    assert "Error: test failed" in result["output"]


def test_normalize_explicit_failure_text():
    raw = {
        "success": False,
        "returncode": 1,
        "stdout": "",
        "stderr": "",
        "failure_text": "Execution failed",
    }

    result = normalize_execution_result(raw)

    assert result["success"] is False
    assert result["status"] == "failure"
    assert result["failure_text"] == "Execution failed"


def test_normalize_success_with_changed_files():
    raw = {
        "success": True,
        "returncode": 0,
        "stdout": "Task completed",
        "stderr": "",
        "changed_files": ["file1.py", "file2.py"],
    }

    result = normalize_execution_result(raw)

    assert result["success"] is True
    assert result["status"] == "success"
    assert result["changed_files"] == ["file1.py", "file2.py"]
