from pathlib import Path

def test_bundle_transport_failure_artifact_is_declared() -> None:
    text = Path("agents/run_task.py").read_text(encoding="utf-8")
    assert "_last_agent_file_bundle_error.txt" in text
    assert "no FILE blocks could be parsed" in text

def test_shell_router_parse_failure_message_mentions_empty_bundle() -> None:
    text = Path("agents/lib/shell_router.py").read_text(encoding="utf-8")
    assert "empty bundle transport failure" in text
