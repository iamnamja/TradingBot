from pathlib import Path

def test_shell_router_parse_failure_artifact_is_declared() -> None:
    text = Path("agents/lib/shell_router.py").read_text(encoding="utf-8")
    assert "_last_agent_file_bundle_error.txt" in text
    assert "Bundle parse diagnostics saved to" in text

def test_runtime_artifact_allowlist_includes_bundle_error_file() -> None:
    text = Path("agents/run_task.py").read_text(encoding="utf-8")
    assert "_last_agent_file_bundle_error.txt" in text
