import pathlib

import pytest

import importlib.util
import sys
from pathlib import Path

_RUN_TASK_PATH = Path(__file__).resolve().parents[1] / "agents" / "run_task.py"
_SPEC = importlib.util.spec_from_file_location("agents.run_task", _RUN_TASK_PATH)
assert _SPEC and _SPEC.loader
run_task = importlib.util.module_from_spec(_SPEC)
sys.modules["agents.run_task"] = run_task
_SPEC.loader.exec_module(run_task)


def _policy_text(*lines: str) -> str:
    return "\n".join(["# Task title", "", "## Harness policy", "", *lines]).strip()


def _append_task_text() -> str:
    return _policy_text(
        "- FILE: agents/example.py MODE=EXACT_COPY_PLUS_APPEND_METHOD "
        "ALLOW_NEW_METHOD=simulate_backlog ANCHOR_BEFORE=_parse_task_file("
    )


def _replace_task_text() -> str:
    return _policy_text(
        "- FILE: agents/example.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD "
        "TARGET_METHOD=validate_static_bundle_contracts"
    )


def test_parse_harness_file_policies_parses_append_policy() -> None:
    policies = run_task.parse_harness_file_policies(_append_task_text())

    assert "agents/example.py" in policies
    rules = policies["agents/example.py"]["rules"]
    assert "append_before:def _parse_task_file(" in rules
    assert "allow_methods:simulate_backlog" in rules


def test_parse_harness_file_policies_parses_replace_policy() -> None:
    policies = run_task.parse_harness_file_policies(_replace_task_text())

    assert "agents/example.py" in policies
    rules = policies["agents/example.py"]["rules"]
    assert "replace_method:validate_static_bundle_contracts" in rules


def test_extract_protected_method_targets_parses_append_target() -> None:
    targets = run_task._extract_protected_method_targets(_append_task_text())

    assert len(targets) == 1
    target = targets[0]
    assert target["path"] == "agents/example.py"
    assert target["mode"] == "append"
    assert target["method_name"] == "simulate_backlog"
    assert target["anchor"] == "def _parse_task_file("


def test_extract_protected_method_targets_parses_replace_target() -> None:
    targets = run_task._extract_protected_method_targets(_replace_task_text())

    assert len(targets) == 1
    target = targets[0]
    assert target["path"] == "agents/example.py"
    assert target["mode"] == "replace"
    assert target["method_name"] == "validate_static_bundle_contracts"
    assert "max_changed_lines" not in target or target["max_changed_lines"] is None


def test_apply_method_insertion_inserts_helper_before_anchor_with_context_indentation() -> None:
    original = "\n".join(
        [
            "class Example:",
            "    def existing(self):",
            "        return 1",
            "",
        ]
    ) + "\n"

    method_text = "\n".join(
        [
            "def helper(self):",
            "    return 3",
            "",
        ]
    )

    updated = run_task.apply_method_insertion(
        original,
        "def existing(self):",
        "helper",
        method_text,
    )

    assert "    def helper(self):" in updated
    assert "        return 3" in updated
    assert updated.index("def helper(self):") < updated.index("def existing(self):")
    assert "    def existing(self):" in updated


def test_apply_method_replacement_replaces_existing_method_body() -> None:
    original = "\n".join(
        [
            "class Example:",
            "    def first(self):",
            "        return 1",
            "",
            "    def target(self):",
            "        return 2",
            "",
            "    def last(self):",
            "        return 3",
            "",
        ]
    ) + "\n"

    method_text = "\n".join(
        [
            "def target(self):",
            "    return 200",
            "",
        ]
    )

    updated = run_task.apply_method_replacement(original, "target", method_text)

    assert "        return 200" in updated
    assert "        return 2\n" not in updated
    assert "    def first(self):" in updated
    assert "    def last(self):" in updated


def test_apply_method_replacement_raises_for_missing_target() -> None:
    original = "\n".join(
        [
            "class Example:",
            "    def existing(self):",
            "        return 1",
            "",
        ]
    ) + "\n"

    method_text = "\n".join(
        [
            "def missing(self):",
            "    return 2",
            "",
        ]
    )

    with pytest.raises(run_task.FileBundleError):
        run_task.apply_method_replacement(original, "missing", method_text)


def test_apply_method_insertion_raises_for_missing_anchor() -> None:
    original = "\n".join(
        [
            "class Example:",
            "    def existing(self):",
            "        return 1",
            "",
        ]
    ) + "\n"

    method_text = "\n".join(
        [
            "def helper(self):",
            "    return 3",
            "",
        ]
    )

    with pytest.raises(run_task.FileBundleError):
        run_task.apply_method_insertion(original, "def missing(self):", "helper", method_text)


def test_parse_method_insertion_bundle_raises_for_missing_end_file() -> None:
    malformed = "\n".join(
        [
            "BEGIN_" + "FILE_BUNDLE",
            "FI" + "LE: agents/run_task.py",
            "def helper(self):",
            "    return 3",
            "END_" + "FILE_BUNDLE",
            "",
        ]
    )

    with pytest.raises(run_task.FileBundleError):
        run_task.parse_method_insertion_bundle(
            malformed,
            pathlib.Path("agents/run_task.py"),
            "helper",
        )


def test_request_and_parse_method_insertion_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = "\n".join(
        [
            "BEGIN_METHOD_INSERTION",
            "TARGET_FILE: agents/run_task.py",
            "METHOD_NAME: helper",
            "BEGIN_METHOD",
            "def helper(self):",
            "    return 3",
            "END_METHOD",
            "END_METHOD_INSERTION",
            "",
        ]
    )

    def fake_chat(messages, model, provider):
        return bundle

    monkeypatch.setattr(run_task, "chat", fake_chat)

    result = run_task.request_and_parse_method_insertion(
        messages=[{"role": "user", "content": "please help"}],
        model="model",
        provider="provider",
        last_output_path=pathlib.Path("last_output.txt"),
        expected_path=pathlib.Path("agents/run_task.py"),
        expected_method_name="helper",
    )

    assert result == "def helper(self):\n    return 3\n"


def test_request_and_parse_method_insertion_rejects_file_bundle_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    malformed = "\n".join(
        [
            "BEGIN_" + "FILE_BUNDLE",
            "FI" + "LE: agents/run_task.py",
            "def helper(self):",
            "    return 3",
            "END_" + "FILE",
            "END_" + "FILE_BUNDLE",
            "",
        ]
    )

    def fake_chat(messages, model, provider):
        return malformed

    monkeypatch.setattr(run_task, "chat", fake_chat)

    with pytest.raises(run_task.FileBundleError, match="BEGIN_FILE_BUNDLE"):
        run_task.request_and_parse_method_insertion(
            messages=[{"role": "user", "content": "please help"}],
            model="model",
            provider="provider",
            last_output_path=pathlib.Path("last_output.txt"),
            expected_path=pathlib.Path("agents/run_task.py"),
            expected_method_name="helper",
        )


def test_request_and_parse_method_insertion_raises_for_malformed_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    malformed = "\n".join(
        [
            "BEGIN_" + "FILE_BUNDLE",
            "FI" + "LE: agents/run_task.py",
            "def wrong(self):",
            "    return 3",
            "END_" + "FILE",
            "END_" + "FILE_BUNDLE",
            "",
        ]
    )

    def fake_chat(messages, model, provider):
        return malformed

    monkeypatch.setattr(run_task, "chat", fake_chat)

    with pytest.raises(run_task.FileBundleError):
        run_task.request_and_parse_method_insertion(
            messages=[{"role": "user", "content": "please help"}],
            model="model",
            provider="provider",
            last_output_path=pathlib.Path("last_output.txt"),
            expected_path=pathlib.Path("agents/run_task.py"),
            expected_method_name="helper",
        )
