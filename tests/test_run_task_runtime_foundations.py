from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace


def _load_runtime_modules():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    run_task = importlib.import_module("agents.run_task")
    check_runner = importlib.import_module("agents.lib.check_runner")
    git_ops = importlib.import_module("agents.lib.git_ops")
    provider_client = importlib.import_module("agents.lib.provider_client")
    failure_journal = importlib.import_module("agents.lib.failure_journal")
    task_contracts = importlib.import_module("agents.lib.task_contracts")
    failure_artifacts = importlib.import_module("agents.lib.failure_artifacts")
    shell_router = importlib.import_module("agents.lib.shell_router")
    artifact_quarantine = importlib.import_module("agents.lib.artifact_quarantine")
    batch_state = importlib.import_module("agents.lib.batch_state")
    task_queue = importlib.import_module("agents.lib.task_queue")
    return (
        run_task,
        check_runner,
        git_ops,
        provider_client,
        failure_journal,
        task_contracts,
        failure_artifacts,
        shell_router,
        artifact_quarantine,
        batch_state,
        task_queue,
    )


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    calls: list[tuple[list[str], bool]] = []

    def fake_capture(cmd: list[str]) -> str:
        if cmd == ["git", "status", "--porcelain"]:
            return ""
        if cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return "main"
        if cmd == ["git", "branch", "--list", "feature-x"]:
            return ""
        raise AssertionError(cmd)

    def fake_run(cmd: list[str], check: bool = True):
        calls.append((cmd, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(git_ops, "capture", fake_capture)
    monkeypatch.setattr(git_ops, "run", fake_run)
    run_task.ensure_clean_worktree()
    run_task.ensure_branch("feature-x")
    assert any(cmd == ["git", "checkout", "-b", "feature-x"] for cmd, _ in calls) or any(
        cmd == ["git", "checkout", "-B", "feature-x"] for cmd, _ in calls
    )


def test_check_runner_summary(monkeypatch) -> None:
    run_task, check_runner, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_capture_result(cmd):
        if cmd == ["ruff", "check", "."]:
            return SimpleNamespace(returncode=0, stdout="lint out\n", stderr="")
        if cmd == ["pytest", "-q"]:
            return SimpleNamespace(returncode=1, stdout="test out\n", stderr="test err\n")
        raise AssertionError(cmd)

    monkeypatch.setattr(check_runner, "capture_result", fake_capture_result)
    ok, text = run_task.run_checks()
    assert ok is False
    assert "=== pytest -q ===" in text
    assert "test out" in text


def test_public_surface_still_available() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    assert callable(run_task.default_provider)
    assert callable(run_task.default_model_for_provider)
    assert callable(run_task.chat_openai)
    assert callable(run_task.chat_anthropic)
    assert callable(run_task.chat)
    assert callable(run_task.run)
    assert callable(run_task.capture)
    assert callable(run_task.capture_result)
    assert callable(run_task.ensure_clean_worktree)
    assert callable(run_task.ensure_branch)
    assert callable(run_task.run_checks)
    assert callable(run_task.parse_required_files)
    assert callable(run_task.validate_exact_deliverable_contract)
    assert callable(run_task.keep_runtime_artifacts_requested)


def test_failure_classifier_distinguishes_multiple_categories() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _ = _load_runtime_modules()
    assert (
        failure_journal.classify_failure("tests", "SyntaxError: invalid syntax in generated test")
        == "python_syntax"
    )
    assert (
        failure_journal.classify_failure(
            "bundle_transport", "references invented seam alias failure_journal_export"
        )
        == "seam_contract_mismatch"
    )
    assert (
        failure_journal.classify_failure(
            "policy", "Protected meta file(s) in normal bundle lane"
        )
        == "harness_meta_regression"
    )


def test_failure_remediation_plans_choose_different_paths() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _ = _load_runtime_modules()
    syntax_plan = failure_journal.build_failure_remediation_plan(
        kind="tests",
        message="SyntaxError: invalid syntax",
        category="python_syntax",
        retry_count=1,
        fingerprint="python_syntax:abc",
        raw_failure_snippet="SyntaxError: invalid syntax",
    )
    harness_plan = failure_journal.build_failure_remediation_plan(
        kind="policy",
        message="Protected meta harness lane regression",
        category="harness_meta_regression",
        retry_count=1,
        fingerprint="harness_meta_regression:def",
        raw_failure_snippet="Protected meta harness lane regression",
    )

    assert syntax_plan["chosen_remediation_path"] == "targeted_syntax_repair"
    assert syntax_plan["continue_autonomously"] is True
    assert harness_plan["chosen_remediation_path"] == "manual_patch_lane"
    assert harness_plan["manual_lane_recommended"] is True


def test_batch_state_init_resume_and_mismatch_guards(tmp_path: Path) -> None:
    _, _, _, _, _, _, _, _, _, batch_state, task_queue = _load_runtime_modules()

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / "001.md").write_text("# one\n", encoding="utf-8")
    (tasks_dir / "002.md").write_text("# two\n", encoding="utf-8")

    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = task_queue.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    state = batch_state.initialize_batch_state(
        manifest=manifest,
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=10,
    )
    assert state.current_index == 0
    assert state.event_seq == 0
    assert [item.status for item in state.queue] == ["queued", "queued"]

    state_path = tmp_path / "batch_state.json"
    batch_state.write_batch_state(state_path, state)

    resumed = batch_state.resume_batch_state(
        state_path=state_path,
        manifest=manifest,
        manifest_source="tasks/manifest.json",
        queue=queue,
    )
    assert resumed.manifest_source == "tasks/manifest.json"
    assert resumed.manifest_fingerprint == batch_state.manifest_fingerprint(manifest)

    mismatch_manifest = {"tasks": ["tasks/001.md"]}
    try:
        batch_state.resume_batch_state(
            state_path=state_path,
            manifest=mismatch_manifest,
            manifest_source="tasks/manifest.json",
            queue=queue[:1],
        )
    except batch_state.BatchStateError as exc:
        assert "manifest fingerprint mismatch" in str(exc)
    else:
        raise AssertionError("Expected BatchStateError for manifest mismatch")


def test_batch_state_resume_from_partially_completed_queue(tmp_path: Path) -> None:
    _, _, _, _, _, _, _, _, _, batch_state, task_queue = _load_runtime_modules()

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / "001.md").write_text("# one\n", encoding="utf-8")
    (tasks_dir / "002.md").write_text("# two\n", encoding="utf-8")

    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = task_queue.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = batch_state.initialize_batch_state(
        manifest=manifest,
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )
    state = batch_state.advance_task_status(state, task_index=0, to_status="running", event_ts=2)
    state = batch_state.advance_task_status(state, task_index=0, to_status="completed", event_ts=3)

    state_path = tmp_path / "partial_state.json"
    batch_state.write_batch_state(state_path, state)

    resumed = batch_state.resume_batch_state(
        state_path=state_path,
        manifest=manifest,
        manifest_source="tasks/manifest.json",
        queue=queue,
    )
    assert resumed.current_index == 1
    assert resumed.queue[0].status == "completed"
    assert resumed.queue[1].status == "queued"
    assert resumed.batch_status == "active"


def test_batch_state_transitions_are_deterministic_and_serializable(tmp_path: Path) -> None:
    _, _, _, _, _, _, _, _, _, batch_state, task_queue = _load_runtime_modules()

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / "001.md").write_text("# one\n", encoding="utf-8")

    manifest = {"tasks": ["tasks/001.md"]}
    queue = task_queue.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = batch_state.initialize_batch_state(
        manifest=manifest,
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=5,
    )

    running = batch_state.advance_task_status(state, task_index=0, to_status="running", event_ts=6)
    completed = batch_state.advance_task_status(running, task_index=0, to_status="completed", event_ts=7)

    assert running.event_seq == 1
    assert completed.event_seq == 2
    assert running.queue[0].attempts == 1
    assert completed.current_index == 1
    assert completed.batch_status == "completed"

    payload = completed.to_dict()
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["event_seq"] == 2
    assert decoded["queue"][0]["status"] == "completed"

    try:
        batch_state.advance_task_status(completed, task_index=0, to_status="running", event_ts=8)
    except Exception as exc:
        assert "Invalid queue status transition" in str(exc)
    else:
        raise AssertionError("Expected transition failure for completed -> running")


def test_keep_runtime_artifacts_requested_accepts_cli_or_env(monkeypatch) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    monkeypatch.delenv("TRADINGBOT_KEEP_RUNTIME_ARTIFACTS", raising=False)
    assert run_task.keep_runtime_artifacts_requested(SimpleNamespace(keep_runtime_artifacts=True)) is True
    assert run_task.keep_runtime_artifacts_requested(SimpleNamespace(keep_runtime_artifacts=False)) is False

    monkeypatch.setenv("TRADINGBOT_KEEP_RUNTIME_ARTIFACTS", "1")
    assert run_task.keep_runtime_artifacts_requested(SimpleNamespace(keep_runtime_artifacts=False)) is True


def test_cleanup_runtime_artifacts_respects_user_facing_retention_controls(monkeypatch, capsys) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    observed: dict[str, object] = {}

    def fake_quarantine(paths, **kwargs):
        observed["paths"] = [p.as_posix() for p in paths]
        observed["retain_known_safe"] = kwargs.get("retain_known_safe")
        return {
            "warnings": {
                "quarantined_known_safe": ["_last_agent_model_output.txt"],
                "retained_known_safe": ["_last_agent_model_output.txt"],
                "unknown_artifacts": [],
            },
            "lifecycle": {"known_safe_action": "retained", "unknown_action": "none"},
            "classified": {"known_safe": [], "unknown": []},
            "retained": [],
            "quarantined": [],
            "should_block": False,
        }

    monkeypatch.setattr(run_task, "_KEEP_RUNTIME_ARTIFACTS_FOR_RUN", True)
    monkeypatch.setattr(
        run_task,
        "_artifact_quarantine_exports",
        lambda: {
            "known_safe_artifact_names": run_task.RUNTIME_ARTIFACT_NAMES,
            "quarantine_runtime_artifacts": fake_quarantine,
            "describe_runtime_artifact_lifecycle": lambda decision: [
                "ℹ️ Retained known-safe runtime artifacts (unstaged): _last_agent_model_output.txt"
            ],
        },
    )

    run_task._cleanup_runtime_artifacts_for_commit([Path("_last_agent_model_output.txt")])
    out = capsys.readouterr().out
    assert observed["retain_known_safe"] is True
    assert "Retained known-safe runtime artifacts" in out
