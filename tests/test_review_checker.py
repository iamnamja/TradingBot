from builder.orchestrator.review import ReviewChecker

def test_valid_scoped_change():
    deliverables = ["file1.py", "file2.py"]
    changed_files = ["file1.py"]
    checker = ReviewChecker(deliverables, changed_files)
    verdict = checker.evaluate()
    assert verdict["mergeable"] is True
    assert verdict["reasons"] == []
    assert verdict["warnings"] == []

def test_missing_deliverables_and_unexpected_change():
    deliverables = ["file1.py", "file2.py"]
    changed_files = ["file3.py"]
    checker = ReviewChecker(deliverables, changed_files)
    verdict = checker.evaluate()
    assert verdict["mergeable"] is False
    assert "Missing deliverables: file1.py, file2.py" in verdict["reasons"]
    assert "Unexpected changes: file3.py" in verdict["reasons"]

def test_runtime_artifact_warning_only():
    deliverables = ["file1.py"]
    changed_files = ["file1.py", "logs/error.log"]
    checker = ReviewChecker(deliverables, changed_files)
    verdict = checker.evaluate()
    assert verdict["mergeable"] is True
    assert verdict["warnings"] == ["Detected runtime artifact: logs/error.log"]

def test_multiple_warnings_preserve_input_order():
    deliverables = ["file1.py"]
    changed_files = ["file1.py", "logs/error.log", "temp.cache"]
    checker = ReviewChecker(deliverables, changed_files)
    verdict = checker.evaluate()
    assert verdict["mergeable"] is True
    assert verdict["warnings"] == [
        "Detected runtime artifact: logs/error.log",
        "Detected runtime artifact: temp.cache",
    ]
