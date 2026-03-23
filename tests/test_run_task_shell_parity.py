from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest


def _import_run_task_module() -> Any:
    return importlib.import_module("agents.run_task")


def _write_task_file(tmp_path: Path, body: str = "Implement feature safely") -> Path:
    task_file = tmp_path / "task.md"
    task_file.write_text(body, encoding="utf-8")
    return task_file


def test_provider_wrapper_delegates_to_extracted_module(monkeypatch: pytest.MonkeyPatch) -> None:
    run_task = _import_run_task_module()
    provider_client = importlib.import_module("agents.lib.provider_client")

    def _fake_chat(messages: list[dict[str, str]], model: str, provider: str | None = None) -> str:
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "OK"

    monkeypatch.setattr(provider_client, "chat", _fake_chat)

    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "OK"


def test_parser_policy_and_semantic_wrappers_delegate_to_extracted_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    run_task = _import_run_task_module()
    bundle_parser = importlib.import_module("agents.lib.bundle_parser")
    protected_file_policy = importlib.import_module("agents.lib.protected_file_policy")
    semantic_preflight = importlib.import_module("agents.lib.semantic_preflight")

    calls: dict[str, bool] = {
        "bundle": False,
        "policy": False,
        "semantic": False,
    }

    def _fake_parse_file_bundle(**kwargs: Any) -> dict[str, str]:
        calls["bundle"] = True
        return {"x.txt": "hi\n"}

    def _fake_parse_harness_file_policies(**kwargs: Any) -> dict[str, dict[str, object]]:
        calls["policy"] = True
        return {}

    def _fake_validate_static_bundle_contracts(bundle: dict[str, str], task_text: str) -> tuple[bool, str]:
        calls["semantic"] = True
        return True, ""

    monkeypatch.setattr(bundle_parser, "parse_file_bundle", _fake_parse_file_bundle)
    monkeypatch.setattr(protected_file_policy, "parse_harness_file_policies", _fake_parse_harness_file_policies)
    monkeypatch.setattr(semantic_preflight, "validate_static_bundle_contracts", _fake_validate_static_bundle_contracts)

    assert run_task.parse_file_bundle("BEGIN_FILE_BUNDLE\nEND_FILE_BUNDLE\n") == {"x.txt": "hi\n"}
    assert run_task.parse_harness_file_policies("## Deliverables\n") == {}
    ok, msg = run_task.validate_static_bundle_contracts({}, "task")
    assert (ok, msg) == (True, "")
    assert calls == {"bundle": True, "policy": True, "semantic": True}


def _invoke_main(run_task_mod: Any, task_file: Path, *, push: bool = False) -> int:
    argv = ["run_task.py", str(task_file), "--provider", "openai", "--model", "m", "--max-iters", "1"]
    if push:
        argv.append("--push")
    old_argv = sys.argv[:]
    sys.argv = argv
    try:
        return int(run_task_mod.main())
    finally:
        sys.argv = old_argv


def _patch_shell_flow(monkeypatch: pytest.MonkeyPatch, run_task_mod: Any, call_log: dict[str, Any]) -> None:
    monkeypatch.setattr(run_task_mod, "_load_dotenv_if_available", lambda: None, raising=False)
    monkeypatch.setattr(run_task_mod, "ensure_clean_worktree", lambda: None, raising=False)
    monkeypatch.setattr(run_task_mod, "ensure_branch", lambda _branch: call_log.setdefault("branch_switched", True), raising=False)

    def _fake_capture(cmd: list[str]) -> str:
        if cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return "main"
        if cmd == ["git", "diff", "--cached", "--name-only"]:
            return "tests/test_run_task_shell_parity.py\n"
        return ""

    monkeypatch.setattr(run_task_mod, "capture", _fake_capture, raising=False)
    monkeypatch.setattr(run_task_mod, "parse_required_files", lambda _task_text: [], raising=False)
    monkeypatch.setattr(run_task_mod, "task_requires_material_update", lambda _task_text: False, raising=False)
    monkeypatch.setattr(run_task_mod, "task_allows_unchanged_cli", lambda _task_text: False, raising=False)
    monkeypatch.setattr(run_task_mod, "existing_file_contents", lambda _paths: {}, raising=False)
    monkeypatch.setattr(run_task_mod, "build_messages", lambda *args, **kwargs: [], raising=False)
    monkeypatch.setattr(run_task_mod, "validate_python_syntax", lambda _bundle: (True, ""), raising=False)
    monkeypatch.setattr(run_task_mod, "enforce_required_files", lambda *args, **kwargs: (True, ""), raising=False)
    monkeypatch.setattr(run_task_mod, "enforce_harness_file_policies", lambda *args, **kwargs: (True, ""), raising=False)
    monkeypatch.setattr(run_task_mod, "validate_imports", lambda _bundle: (True, ""), raising=False)
    monkeypatch.setattr(run_task_mod, "snapshot_file_contents", lambda _paths: {}, raising=False)
    monkeypatch.setattr(run_task_mod, "restore_file_snapshot", lambda _snapshot: None, raising=False)
    monkeypatch.setattr(run_task_mod, "write_files", lambda _bundle: call_log.setdefault("files_written", True), raising=False)

    monkeypatch.setattr(run_task_mod, "request_and_parse_bundle", lambda *args, **kwargs: {"x.txt": "hi\n"}, raising=False)

    monkeypatch.setattr(run_task_mod, "run", lambda *_args, **_kwargs: None, raising=False)

    def _cleanup(paths: list[Path]) -> None:
        call_log["cleanup_called"] = [p.as_posix() for p in paths]

    monkeypatch.setattr(run_task_mod, "_cleanup_runtime_artifacts_for_commit", _cleanup, raising=False)


def test_shell_green_and_push_cleanup_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_task_mod = _import_run_task_module()
    task_file = _write_task_file(tmp_path)
    call_log: dict[str, Any] = {}

    _patch_shell_flow(monkeypatch, run_task_mod, call_log)
    monkeypatch.setattr(run_task_mod, "run_checks", lambda *args, **kwargs: (True, "ok"), raising=False)

    rc = _invoke_main(run_task_mod, task_file, push=True)

    assert rc == 0
    assert call_log.get("files_written") is True
    cleanup_called = call_log.get("cleanup_called")
    assert cleanup_called is not None
    assert "_last_agent_model_output.txt" in cleanup_called
    assert "_last_agent_file_bundle.txt" in cleanup_called


def test_shell_failing_path_returns_nonzero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_task_mod = _import_run_task_module()
    task_file = _write_task_file(tmp_path, body="Do something impossible")
    call_log: dict[str, Any] = {}

    _patch_shell_flow(monkeypatch, run_task_mod, call_log)
    monkeypatch.setattr(run_task_mod, "run_checks", lambda *args, **kwargs: (False, "failed"), raising=False)

    rc = _invoke_main(run_task_mod, task_file, push=False)

    assert rc != 0


def test_shell_convergence_targets_are_defined_once() -> None:
    run_task_mod = _import_run_task_module()
    source = Path(run_task_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    counts: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            counts[node.name] = counts.get(node.name, 0) + 1

    assert counts.get("default_provider") == 1
    assert counts.get("run_checks") == 1
    assert counts.get("_spec_mode_exports") == 1


def test_repo_root_bootstrap_precedes_agents_lib_imports() -> None:
    run_task_mod = _import_run_task_module()
    source = Path(run_task_mod.__file__).read_text(encoding="utf-8")

    bootstrap_idx = source.index("_ensure_repo_root_on_sys_path()")
    lib_import_idx = source.index("from agents.lib import")
    assert bootstrap_idx < lib_import_idx


def test_spec_mode_exports_preserve_execution_resolvers() -> None:
    run_task_mod = _import_run_task_module()
    exports = run_task_mod._spec_mode_exports()

    assert set(exports) >= {
        "spec_mode",
        "task_is_underspecified",
        "build_frozen_spec_artifact",
        "write_frozen_spec_artifact",
        "read_frozen_spec_artifact",
        "resolve_execution_task_text",
    }
