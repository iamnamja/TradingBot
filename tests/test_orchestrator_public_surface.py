from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    for candidate in (str(root), str(src)):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def test_public_surface_ownership_and_shell_exports() -> None:
    _ensure_repo_on_path()
    cfg_module = importlib.import_module("builder.orchestrator.project_config")
    adapter_module = importlib.import_module("builder.orchestrator.project_adapter")
    run_task = importlib.import_module("agents.run_task")

    assert hasattr(cfg_module, "bootstrap_project_config_scaffold")
    assert hasattr(adapter_module, "bootstrap_project_adapter_scaffold")
    assert hasattr(adapter_module, "build_bootstrap_starter_docs_text")
    assert hasattr(adapter_module, "build_bootstrap_task_template_text")

    exports = run_task._bootstrap_exports()
    assert list(exports) == [
        "bootstrap_project_config_scaffold",
        "bootstrap_project_adapter_scaffold",
    ]
    assert callable(exports["bootstrap_project_config_scaffold"])
    assert callable(exports["bootstrap_project_adapter_scaffold"])

    assert callable(run_task.enforce_meta_file_task_gate)
    assert callable(run_task._normalize_policy_path)
    assert callable(run_task._task_baseline_paths)
    assert callable(run_task.request_and_parse_bundle)

    shell_exports = run_task._shell_router_exports()
    assert callable(shell_exports["build_shell_seam_registry"])
    assert callable(shell_exports["shell_seam_exports"])
    assert callable(shell_exports["route_shell_main"])

    registry = shell_exports["shell_seam_exports"]()
    assert registry["bootstrap"] == ("_bootstrap_exports",)
    assert registry["failure_journal"] == ("_report_failure",)
    assert registry["validator_runner"] == ("run_checks", "validate_python_syntax", "validate_imports")
    assert registry["artifact_quarantine"] == (
        "_cleanup_runtime_artifacts_for_commit",
        "_runtime_artifact_paths",
        "restore_file_snapshot",
    )
    assert registry["shell_router"] == (
        "build_messages",
        "build_method_insertion_messages",
        "request_and_parse_bundle",
        "request_and_parse_method_insertion",
        "apply_method_insertion",
        "apply_method_replacement",
        "FILE_BUNDLE_BEGIN",
        "FILE_END",
        "FILE_BUNDLE_END",
    )


def test_generic_default_config_compatibility_freeze() -> None:
    _ensure_repo_on_path()
    from builder.orchestrator.project_adapter import ProjectAdapter

    cfg = ProjectAdapter.get_generic_project_config()
    assert cfg.state_path is None
    assert cfg.audit_path is None
    assert cfg.task_file_pattern == "*.task.md"
    assert cfg.artifact_path_patterns == ["generic_artifacts/*"]
    assert cfg.approval_required_file_patterns == ["README.md"]


def test_validator_default_path_is_legacy_non_plugin(monkeypatch) -> None:
    _ensure_repo_on_path()
    validator_runner = importlib.import_module("agents.lib.validator_runner")

    called = {"plugin": False}

    def _boom(*args, **kwargs):
        called["plugin"] = True
        raise AssertionError("plugin path must not run for config=None")

    monkeypatch.setattr(validator_runner, "run_validator", _boom)
    monkeypatch.setattr(
        validator_runner.check_runner,
        "run_checks",
        lambda: (True, ""),
    )

    ok, output = validator_runner.run_checks(None)
    assert ok is True
    assert output == ""
    assert called["plugin"] is False


def test_meta_file_lane_gate_live_core_set_remains_blocked() -> None:
    _ensure_repo_on_path()
    run_task = importlib.import_module("agents.run_task")

    for path in (
        "agents/run_task.py",
        "agents/lib/shell_router.py",
        "agents/lib/bundle_parser.py",
        "agents/lib/protected_file_policy.py",
    ):
        ok, msg = run_task.enforce_meta_file_task_gate([path], forbidden_paths=None)
        assert ok is False
        assert "Protected meta file(s) in normal bundle lane" in msg
        assert path in msg
