from __future__ import annotations

import json
from pathlib import Path


def test_bundle_transport_failure_artifact_is_declared() -> None:
    text = Path("agents/run_task.py").read_text(encoding="utf-8")
    assert "_last_agent_file_bundle_error.txt" in text
    assert "no FILE blocks could be parsed" in text


def test_shell_router_parse_failure_message_mentions_empty_bundle() -> None:
    text = Path("agents/lib/shell_router.py").read_text(encoding="utf-8")
    assert "empty bundle transport failure" in text


def _read_capture_result(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_capture_result_zero_length_is_explicit(tmp_path: Path) -> None:
    # Simulate zero-length raw output capture
    last_output = tmp_path / "last_output.txt"
    last_output.write_text("", encoding="utf-8")
    last_bundle = tmp_path / "bundle.txt"

    import agents.run_task as run_task

    # Emit failure artifacts (placeholders + capture-result)
    run_task._emit_failure_artifact_messages(
        last_output_path=last_output,
        last_bundle_path=last_bundle,
        create_placeholders=True,
        task_file="tasks/191.md",
        failure_category="bundle_transport",
        before_model_output=False,
        normal_bundle_attempted=True,
        reason="testing zero-length",
    )

    capture_result_path = last_output.with_name("_last_raw_output_capture_result.json")
    assert capture_result_path.exists()
    payload = _read_capture_result(capture_result_path)
    assert payload["status"] == "empty_zero_length"
    assert payload["raw_output_length"] == 0
    assert payload["raw_output_nonempty"] is False
    assert payload["raw_output_whitespace_only"] is False


def test_capture_result_whitespace_only_is_explicit(tmp_path: Path) -> None:
    # Simulate whitespace-only raw output capture
    last_output = tmp_path / "last_output.txt"
    last_output.write_text("   \n\t", encoding="utf-8")
    last_bundle = tmp_path / "bundle.txt"

    import agents.run_task as run_task

    run_task._emit_failure_artifact_messages(
        last_output_path=last_output,
        last_bundle_path=last_bundle,
        create_placeholders=True,
        task_file="tasks/191.md",
        failure_category="bundle_transport",
        before_model_output=False,
        normal_bundle_attempted=True,
        reason="testing whitespace-only",
    )

    capture_result_path = last_output.with_name("_last_raw_output_capture_result.json")
    assert capture_result_path.exists()
    payload = _read_capture_result(capture_result_path)
    assert payload["status"] == "empty_whitespace_only"
    assert payload["raw_output_length"] > 0
    assert payload["raw_output_nonempty"] is False
    assert payload["raw_output_whitespace_only"] is True


def test_capture_result_non_empty_is_explicit(tmp_path: Path) -> None:
    # Simulate non-empty raw output capture
    last_output = tmp_path / "last_output.txt"
    last_output.write_text("non-empty", encoding="utf-8")
    last_bundle = tmp_path / "bundle.txt"

    import agents.run_task as run_task

    run_task._emit_failure_artifact_messages(
        last_output_path=last_output,
        last_bundle_path=last_bundle,
        create_placeholders=True,
        task_file="tasks/191.md",
        failure_category="bundle_transport",
        before_model_output=False,
        normal_bundle_attempted=True,
        reason="testing non-empty",
    )

    capture_result_path = last_output.with_name("_last_raw_output_capture_result.json")
    assert capture_result_path.exists()
    payload = _read_capture_result(capture_result_path)
    assert payload["status"] == "non_empty"
    assert payload["raw_output_length"] >= len("non-empty")
    assert payload["raw_output_nonempty"] is True
    assert payload["raw_output_whitespace_only"] is False
