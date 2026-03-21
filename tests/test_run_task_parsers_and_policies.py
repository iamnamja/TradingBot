from __future__ import annotations

import pytest

from agents import run_task


def _bundle_text() -> str:
    return (
        "BEGIN_" + "FILE_BUNDLE\n"
        "FI" + "LE: a.py\n"
        "x = 1\n"
        "END_" + "FILE\n"
        "FI" + "LE: b.txt\n"
        "hello\n"
        "END_" + "FILE\n"
        "END_" + "FILE_BUNDLE\n"
    )


def test_parse_file_bundle_parity_normal() -> None:
    parsed = run_task.parse_file_bundle(_bundle_text())
    assert parsed == {"a.py": "x = 1\n", "b.txt": "hello\n"}


def test_parse_file_bundle_parity_malformed_nested_header() -> None:
    text = (
        "BEGIN_" + "FILE_BUNDLE\n"
        "FI" + "LE: a.py\n"
        "FI" + "LE: b.py\n"
        "END_" + "FILE\n"
        "END_" + "FILE_BUNDLE\n"
    )
    with pytest.raises(run_task.FileBundleError):
        run_task.parse_file_bundle(text)


def test_parse_method_insertion_bundle_parity() -> None:
    text = (
        "BEGIN_" + "METHOD_INSERTION\n"
        "TARGET_FILE: agents/run_task.py\n"
        "METHOD_NAME: demo_method\n"
        "BEGIN_" + "METHOD\n"
        "def demo_method(x):\n"
        "    return x\n"
        "END_" + "METHOD\n"
        "END_" + "METHOD_INSERTION\n"
    )
    out = run_task.parse_method_insertion_bundle(text, "agents/run_task.py", "demo_method")
    assert out == "def demo_method(x):\n    return x\n"


def test_parse_task_contract_directives_parity() -> None:
    task = (
        "## Machine-Readable Contract Directives\n"
        "- CONSTRUCTOR: pkg.Class(a,b)\n"
        "- ALLOWED_METHODS: pkg.Class run\n"
        "- RESULT_KEYS: fn alpha beta\n"
    )
    parsed = run_task.parse_task_contract_directives(task)
    assert parsed == {
        "CONSTRUCTOR": ["pkg.Class(a,b)"],
        "ALLOWED_METHODS": ["pkg.Class run"],
        "RESULT_KEYS": ["fn alpha beta"],
    }


def test_parse_harness_file_policies_parity() -> None:
    task = (
        "## Harness policy\n"
        "- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=parse_file_bundle\n"
        "HARNESS_POLICY: agents/run_task.py max_changed_lines:40\n"
    )
    parsed = run_task.parse_harness_file_policies(task)
    assert "agents/run_task.py" in parsed
    rules = parsed["agents/run_task.py"]["rules"]
    assert "replace_method:parse_file_bundle" in rules
    assert "allow_methods:parse_file_bundle" in rules
    assert "max_changed_lines:40" in rules


def test_extract_protected_method_targets_parity() -> None:
    task = (
        "## Deliverables\n"
        "- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD "
        "ALLOW_NEW_METHOD=_parser_policy_exports ANCHOR_BEFORE=if __name__ == \"__main__\":\n"
        "- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=parse_file_bundle\n"
    )
    targets = run_task._extract_protected_method_targets(task)
    assert {
        "path": "agents/run_task.py",
        "mode": "append",
        "anchor": "if __name__ == \"__main__\":",
        "method_name": "_parser_policy_exports",
        "max_changed_lines": None,
    } in targets
    assert {
        "path": "agents/run_task.py",
        "mode": "replace",
        "method_name": "parse_file_bundle",
        "max_changed_lines": None,
    } in targets
