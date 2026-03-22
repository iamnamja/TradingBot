from __future__ import annotations

from pathlib import Path

from agents.lib import spec_mode


SAMPLE_TASK = """
# Task X

## Goal
- Add spec mode support.

## Required behavior
- capture scope
- capture edge cases
- capture forbidden patterns
- capture acceptance criteria
- capture verification commands
- capture expected outputs

## Forbidden patterns
- Do not perform implementation work.
- Never replace current shell contract.

## Acceptance criteria
- frozen spec artifact is deterministic
- pytest -q is green

## Verification commands
- `ruff check .`
- `pytest -q`

## Output requirements
- include stable fields
"""


def test_underspecified_input_generates_structured_artifact() -> None:
    task = """
# Minimal task
Build something useful.
"""
    artifact = spec_mode.build_frozen_spec_artifact(task, "tasks/minimal.md", force=True)
    frozen = artifact["frozen_spec"]
    assert artifact["mode"] == "spec"
    assert artifact["task_path"] == "tasks/minimal.md"
    assert isinstance(frozen, dict)
    assert "scope" in frozen
    assert "forbidden_patterns" in frozen
    assert "acceptance_criteria" in frozen
    assert "verification_commands" in frozen
    assert "expected_outputs" in frozen


def test_frozen_artifact_is_deterministic() -> None:
    a1 = spec_mode.build_frozen_spec_artifact(SAMPLE_TASK, "tasks/x.md")
    a2 = spec_mode.build_frozen_spec_artifact(SAMPLE_TASK, "tasks/x.md")
    assert a1 == a2
    assert a1["source_hash"] == a2["source_hash"]


def test_spec_mode_logic_lives_in_lib_module() -> None:
    assert hasattr(spec_mode, "task_is_underspecified")
    assert hasattr(spec_mode, "build_frozen_spec_artifact")
    assert hasattr(spec_mode, "write_frozen_spec_artifact")


def test_write_frozen_spec_artifact(tmp_path: Path) -> None:
    artifact = spec_mode.build_frozen_spec_artifact(SAMPLE_TASK, "tasks/x.md")
    out_path = tmp_path / "artifacts" / "spec_mode" / "frozen_spec.json"
    spec_mode.write_frozen_spec_artifact(artifact, out_path)
    text = out_path.read_text(encoding="utf-8")
    assert '"mode": "spec"' in text
    assert '"frozen_spec"' in text
