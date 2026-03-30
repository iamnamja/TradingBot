from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace


REQUIRED_FAILURE_JOURNAL_KEYS = {
    "failure_journal",
    "classify_failure",
    "failure_fingerprint",
    "bounded_failure_snippet",
    "recommended_next_action",
    "chosen_remediation_path",
    "append_failure_journal_entry",
    "retry_count_for_fingerprint",
}
FORBIDDEN_FAILURE_JOURNAL_KEYS = {
    "module",
    "report_failure",
    "write_failure_journal",
    "build_failure_journal_entry",
    "load_failure_journal_entries",
    "build_failure_entry",
}


def _ensure_repo_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    for candidate in (str(root), str(src)):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def _load_modules():
    _ensure_repo_on_path()
    run_task = importlib.import_module("agents.run_task")
    spec_mode = importlib.import_module("agents.lib.spec_mode")
    validator_runner = importlib.import_module("agents.lib.validator_runner")
    return run_task, spec_mode, validator_runner


def test_integrated_spec_mode_validator_failure_and_failure_journal_exports(
    tmp_path: Path, monkeypatch
) -> None:
    run_task, spec_mode, validator_runner = _load_modules()

    live_task_text = "Implement integrated scenario.\n\n"
    artifact = spec_mode.build_frozen_spec_artifact(
        live_task_text,
        "tasks/062_integrated.md",
        force=True,
    )
    artifact_path = tmp_path / "frozen_spec.json"
    spec_mode.write_frozen_spec_artifact(artifact, artifact_path)

    resolved = spec_mode.resolve_execution_task_text("IGNORED\n", str(artifact_path))

    assert isinstance(resolved, dict)
    assert resolved.get("resolved_from_frozen") is True
    assert resolved.get("task_text") == "Implement integrated scenario."

    validators = (
        {
            "name": "plugin:deterministic",
            "command": "python -m deterministic",
            "enabled": True,
            "required": True,
        },
    )
    monkeypatch.setattr(
        validator_runner,
        "_resolve_config",
        lambda _config: SimpleNamespace(validators=validators),
    )
    monkeypatch.setattr(
        validator_runner,
        "_run_plugin_validators",
        lambda _validators, runner=None: (False, "simulated validator failure"),
    )

    ok, output = validator_runner.run_checks(config="ignored")

    assert ok is False
    assert "simulated validator failure" in output

    exports = run_task._failure_journal_exports()
    assert REQUIRED_FAILURE_JOURNAL_KEYS.issubset(exports.keys())
    assert FORBIDDEN_FAILURE_JOURNAL_KEYS.isdisjoint(exports.keys())
