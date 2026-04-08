from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_run_task_module():
    path = Path("agents/run_task.py")
    spec = importlib.util.spec_from_file_location("agents_run_task_testmod", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_spec_artifact_mode_value_stays_compat():
    mod = _load_run_task_module()
    exports = mod._spec_mode_exports()
    build = exports["build_frozen_spec_artifact"]
    artifact = build("# Minimal\ndo x\n", "tasks/x.md", force=True)
    assert artifact["mode"] == "spec"
    assert "frozen_spec" in artifact


def test_execution_resolves_from_frozen_artifact(monkeypatch, tmp_path, capsys):
    mod = _load_run_task_module()
    exports = mod._spec_mode_exports()
    build = exports["build_frozen_spec_artifact"]

    canonical = "# Canonical task\n- do deterministic thing\n"
    artifact = build(canonical, "tasks/demo.md", force=True)
    artifact_path = tmp_path / "frozen.json"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    captured = {"task_text": None}

    def fake_parse_required_files(task_text: str):
        captured["task_text"] = task_text
        return []

    monkeypatch.setitem(mod.main.__globals__, "ensure_clean_worktree", lambda: None)
    monkeypatch.setitem(mod.main.__globals__, "ensure_branch", lambda _branch: None)
    monkeypatch.setitem(mod.main.__globals__, "capture", lambda _cmd: "main")
    monkeypatch.setitem(mod.main.__globals__, "parse_required_files", fake_parse_required_files)
    monkeypatch.setitem(mod.main.__globals__, "parse_harness_file_policies", lambda _t: {})
    monkeypatch.setitem(mod.main.__globals__, "_extract_protected_method_targets", lambda _t: [])
    monkeypatch.setitem(mod.main.__globals__, "existing_file_contents", lambda _p: {})
    monkeypatch.setitem(mod.main.__globals__, "request_and_parse_bundle", lambda *a, **k: {})
    monkeypatch.setitem(mod.main.__globals__, "write_files", lambda _f: None)
    monkeypatch.setitem(mod.main.__globals__, "run_checks", lambda: (True, ""))
    monkeypatch.setitem(mod.main.__globals__, "snapshot_file_contents", lambda _p: {})
    monkeypatch.setitem(mod.main.__globals__, "restore_file_snapshot", lambda _s: None)

    old_argv = sys.argv[:]
    try:
        sys.argv = ["run_task.py", str(artifact_path), "--max-iters", "1"]
        code = mod.main()
    finally:
        sys.argv = old_argv

    out = capsys.readouterr().out
    assert code == 0
    assert "Execution mode: using frozen spec artifact" in out
    assert captured["task_text"] == canonical.strip()


def test_proof_task_missing_exact_files_is_rejected_before_model_execution(monkeypatch, tmp_path, capsys):
    mod = _load_run_task_module()
    task_path = tmp_path / "tasks" / "130_supervised_portfolio_reproof.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "# Task 130 — supervised portfolio re-proof\n\n"
        "## Deliverables\n"
        "- `README.md`\n"
        "- `docs/TRADINGBOT_PROJECT_STATE.md`\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(mod.main.__globals__, "ensure_clean_worktree", lambda: None)
    monkeypatch.setitem(mod.main.__globals__, "capture", lambda _cmd: "main")
    monkeypatch.setitem(mod.main.__globals__, "ensure_branch", lambda _branch: (_ for _ in ()).throw(AssertionError("should not create branch")))
    monkeypatch.setitem(mod.main.__globals__, "request_and_parse_bundle", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not reach model request")))

    old_argv = sys.argv[:]
    try:
        sys.argv = ["run_task.py", str(task_path), "--max-iters", "1"]
        code = mod.main()
    finally:
        sys.argv = old_argv

    out = capsys.readouterr().out
    assert code == 1
    assert "[task_admission]" in out
    assert "Create or update these exact files" in out
    assert (tmp_path / "_last_agent_model_output.txt").exists()
    assert (tmp_path / "_last_agent_file_bundle.txt").exists()
