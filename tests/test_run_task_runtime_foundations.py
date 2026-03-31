from __future__ import annotations

import importlib
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
    seam_plan = failure_journal.build_failure_remediation_plan(
        kind="bundle_transport",
        message="references invented seam alias failure_journal_export",
        category="seam_contract_mismatch",
        retry_count=1,
        fingerprint="seam_contract_mismatch:def",
        raw_failure_snippet="references invented seam alias failure_journal_export",
    )
    meta_plan = failure_journal.build_failure_remediation_plan(
        kind="policy",
        message="Protected meta file(s) in normal bundle lane",
        category="harness_meta_regression",
        retry_count=1,
        fingerprint="harness_meta_regression:ghi",
        raw_failure_snippet="Protected meta file(s) in normal bundle lane",
    )
    assert syntax_plan["chosen_remediation_path"] == "targeted_syntax_repair"
    assert syntax_plan["continue_autonomously"] is True
    assert seam_plan["chosen_remediation_path"] == "semantic_contract_repair"
    assert seam_plan["continue_autonomously"] is False
    assert meta_plan["chosen_remediation_path"] == "manual_patch_lane"
    assert meta_plan["manual_lane_recommended"] is True


def test_report_failure_records_confidence_and_plan(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, failure_journal, _, _, _, _, _, _ = _load_runtime_modules()
    monkeypatch.setenv("TRADINGBOT_FAILURE_JOURNAL_PATH", str(tmp_path / "journal.jsonl"))
    monkeypatch.setenv("TRADINGBOT_TASK_ID", "task-056")
    run_task._report_failure(
        "bundle_transport", "references invented seam alias failure_journal_export"
    )
    rows = failure_journal.read_failure_journal(tmp_path / "journal.jsonl")
    assert rows
    last = rows[-1]
    assert last["failure_category"] == "seam_contract_mismatch"
    assert last["chosen_remediation_path"] == "semantic_contract_repair"
    assert isinstance(last["autonomy_confidence"], float)
    assert last["continue_autonomously"] is False


def test_task_contract_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    run_task, _, _, _, _, task_contracts, _, _, _, _, _ = _load_runtime_modules()

    def fake_parse(task_text: str):
        assert (
            task_text
            == "## Create or update these exact files\n- `docs/TRADINGBOT_PROJECT_STATE.md`\n"
        )
        return ["docs/TRADINGBOT_PROJECT_STATE.md"]

    monkeypatch.setattr(task_contracts, "parse_required_files_from_task_text", fake_parse)
    assert run_task.parse_required_files(
        "## Create or update these exact files\n- `docs/TRADINGBOT_PROJECT_STATE.md`\n"
    ) == ["docs/TRADINGBOT_PROJECT_STATE.md"]


def test_validate_exact_deliverable_contract_delegates_to_extracted_module(monkeypatch) -> None:
    run_task, _, _, _, _, task_contracts, _, _, _, _, _ = _load_runtime_modules()
    monkeypatch.setattr(
        task_contracts,
        "exact_deliverable_contract_issues",
        lambda task_text: ["`../outside.md` uses path traversal and is not allowed."],
    )
    ok, msg = run_task.validate_exact_deliverable_contract("task")
    assert ok is False
    assert "Invalid exact deliverable contract entries detected:" in msg
    assert "path traversal" in msg


def test_enforce_required_files_reports_final_acceptance_gap() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    ok, msg = run_task.enforce_required_files(
        ["agents/run_task.py", "docs/TRADINGBOT_PROJECT_STATE.md"],
        {"agents/run_task.py": "updated"},
    )
    assert ok is False
    assert "parsed from task contract" in msg
    assert "missing from final accepted result after lane reconciliation" in msg
    assert "docs/TRADINGBOT_PROJECT_STATE.md" in msg


def test_artifact_quarantine_retention_control_is_available() -> None:
    _, _, _, _, _, _, _, _, artifact_quarantine, _, _ = _load_runtime_modules()

    result = artifact_quarantine.quarantine_runtime_artifacts(
        [Path("_last_agent_model_output.txt")],
        run_git_command=lambda *args, **kwargs: None,
        path_exists=lambda _p: False,
        unlink_path=lambda _p: None,
        retain_known_safe=True,
    )

    assert result["warnings"]["quarantined_known_safe"] == ["_last_agent_model_output.txt"]
    assert result["warnings"]["retained_known_safe"] == ["_last_agent_model_output.txt"]
    assert result["lifecycle"]["known_safe_action"] == "retained"


def test_batch_state_initialize_resume_and_transition_determinism(tmp_path: Path) -> None:
    _, _, _, _, _, _, _, _, _, batch_state, task_queue = _load_runtime_modules()

    task_file_1 = tmp_path / "tasks" / "001.md"
    task_file_2 = tmp_path / "tasks" / "002.md"
    task_file_1.parent.mkdir(parents=True, exist_ok=True)
    task_file_1.write_text("# one\n", encoding="utf-8")
    task_file_2.write_text("# two\n", encoding="utf-8")

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
    assert state.queue[0].status == "queued"

    state = batch_state.advance_task_status(state, task_index=0, to_status="running", event_ts=11)
    state = batch_state.advance_task_status(state, task_index=0, to_status="completed", event_ts=12)
    assert state.current_index == 1
    assert state.event_seq == 2
    assert state.queue[0].status == "completed"
    assert state.queue[0].attempts == 1

    path = tmp_path / "batch_state.json"
    batch_state.write_batch_state(path, state)
    resumed = batch_state.resume_batch_state(
        state_path=path,
        manifest=manifest,
        manifest_source="tasks/manifest.json",
    )
    assert resumed.current_index == 1
    assert resumed.queue[0].status == "completed"
