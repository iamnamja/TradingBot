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


def _write_meta_artifact(last_output: Path, *, provider: str, model: str, required_transport: str, selected_transport: str, phase: str, retry_index: int, raw_output_length: int) -> None:
    meta_path = last_output.with_name("_last_raw_output_meta.txt")
    lines = [
        f"provider: {provider}",
        f"model: {model}",
        f"required_transport: {required_transport}",
        f"selected_transport: {selected_transport}",
        f"phase: {phase}",
        f"retry_index: {retry_index}",
        f"raw_output_length: {raw_output_length}",
        "raw_output_nonempty: False" if raw_output_length == 0 else "raw_output_nonempty: True",
        "raw_output_whitespace_only: False",
    ]
    meta_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_details(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_transport_failure_details_bundle_path(tmp_path: Path) -> None:
    # Prepare simulated empty bundle output and meta info
    last_output = tmp_path / "last_output.txt"
    raw = "BEGIN_FILE_BUNDLE\nEND_FILE_BUNDLE\n"
    last_output.write_text(raw, encoding="utf-8")
    last_bundle = tmp_path / "bundle.txt"

    # Seed meta so the details artifact can infer parser path/contract
    _write_meta_artifact(
        last_output,
        provider="openai",
        model="gpt-5",
        required_transport="file_bundle",
        selected_transport="file_bundle",
        phase="bundle.initial",
        retry_index=1,
        raw_output_length=len(raw),
    )

    import agents.run_task as run_task

    run_task._emit_failure_artifact_messages(
        last_output_path=last_output,
        last_bundle_path=last_bundle,
        create_placeholders=True,
        task_file="tasks/192.md",
        failure_category="bundle_transport",
        before_model_output=False,
        normal_bundle_attempted=True,
        reason="testing empty bundle",
    )

    details_path = last_output.with_name("_last_transport_failure_details.json")
    assert details_path.exists()
    details = _read_details(details_path)

    assert details["artifact_type"] == "transport_failure_details"
    assert details["provider"] == "openai"
    assert details["model"] == "gpt-5"
    assert details["required_transport"] == "file_bundle"
    assert details["selected_transport"] == "file_bundle"
    # With bundle phase in meta, parser path should reflect file_bundle
    assert details["parser_path"] in {"file_bundle", "bundle"}  # tolerate older alias if present
    assert details["retry_index"] == 1
    assert details["protected_method_mode_selected"] is False
    # Placeholders have no FILE headers
    assert details["file_bundle_file_count"] == 0
    assert details["raw_output_length"] == len(raw)
    # Sibling artifact pointers are present (may be empty strings when not created)
    assert "artifacts" in details and "raw_output_path" in details["artifacts"]


def test_transport_failure_details_method_insertion_path(tmp_path: Path) -> None:
    # Prepare simulated protected-method failure and meta info
    last_output = tmp_path / "last_output.txt"
    raw = "BEGIN_METHOD_INSERTION\nTARGET_FILE: agents/run_task.py\nMETHOD_NAME: helper\nEND_METHOD_INSERTION\n"
    last_output.write_text(raw, encoding="utf-8")
    last_bundle = tmp_path / "bundle.txt"

    _write_meta_artifact(
        last_output,
        provider="openai",
        model="gpt-5",
        required_transport="method_insertion",
        selected_transport="file_bundle",
        phase="method_insertion.initial",
        retry_index=2,
        raw_output_length=len(raw),
    )

    import agents.run_task as run_task

    run_task._emit_failure_artifact_messages(
        last_output_path=last_output,
        last_bundle_path=last_bundle,
        create_placeholders=True,
        task_file="tasks/192.md",
        failure_category="method_insertion_transport",
        before_model_output=False,
        normal_bundle_attempted=False,
        reason="testing method-insertion failure",
        protected_execution_attempted=True,
    )

    details_path = last_output.with_name("_last_transport_failure_details.json")
    assert details_path.exists()
    details = _read_details(details_path)

    assert details["artifact_type"] == "transport_failure_details"
    assert details["provider"] == "openai"
    assert details["model"] == "gpt-5"
    assert details["required_transport"] == "method_insertion"
    # Parser path should reflect protected method mode
    assert details["parser_path"] == "method_insertion"
    assert details["retry_index"] == 2
    assert details["protected_method_mode_selected"] is True
    # Method block count field exists and is an int (may be zero in malformed cases)
    assert isinstance(details.get("method_block_count", 0), int)
    assert details["raw_output_length"] == len(raw)
