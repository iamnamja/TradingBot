from __future__ import annotations

import importlib
import os
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
    return run_task, check_runner, git_ops, provider_client, failure_journal, task_contracts, failure_artifacts, shell_router


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _, _, _, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _, _, _, _ = _load_runtime_modules()
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
    run_task, check_runner, _, _, _, _, _, _ = _load_runtime_modules()

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
    run_task, _, _, _, _, _, _, _ = _load_runtime_modules()
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


def test_failure_classifier_distinguishes_multiple_categories() -> None:
    _, _, _, _, failure_journal, _, _, _ = _load_runtime_modules()
    assert failure_journal.classify_failure("tests", "SyntaxError: invalid syntax in generated test") == "python_syntax"
    assert failure_journal.classify_failure("bundle_transport", "references invented seam alias failure_journal_export") == "seam_contract_mismatch"
    assert failure_journal.classify_failure("policy", "Protected meta file(s) in normal bundle lane") == "harness_meta_regression"


def test_failure_remediation_plans_choose_different_paths() -> None:
    _, _, _, _, failure_journal, _, _, _ = _load_runtime_modules()
    syntax_plan = failure_journal.build_failure_remediation_plan(kind="tests", message="SyntaxError: invalid syntax", category="python_syntax", retry_count=1, fingerprint="python_syntax:abc", raw_failure_snippet="SyntaxError: invalid syntax")
    seam_plan = failure_journal.build_failure_remediation_plan(kind="bundle_transport", message="references invented seam alias failure_journal_export", category="seam_contract_mismatch", retry_count=1, fingerprint="seam_contract_mismatch:def", raw_failure_snippet="references invented seam alias failure_journal_export")
    meta_plan = failure_journal.build_failure_remediation_plan(kind="policy", message="Protected meta file(s) in normal bundle lane", category="harness_meta_regression", retry_count=1, fingerprint="harness_meta_regression:ghi", raw_failure_snippet="Protected meta file(s) in normal bundle lane")
    assert syntax_plan["chosen_remediation_path"] == "targeted_syntax_repair"
    assert syntax_plan["continue_autonomously"] is True
    assert seam_plan["chosen_remediation_path"] == "semantic_contract_repair"
    assert seam_plan["continue_autonomously"] is False
    assert meta_plan["chosen_remediation_path"] == "manual_patch_lane"
    assert meta_plan["manual_lane_recommended"] is True


def test_report_failure_records_confidence_and_plan(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, failure_journal, _, _, _ = _load_runtime_modules()
    monkeypatch.setenv("TRADINGBOT_FAILURE_JOURNAL_PATH", str(tmp_path / "journal.jsonl"))
    monkeypatch.setenv("TRADINGBOT_TASK_ID", "task-056")
    run_task._report_failure("bundle_transport", "references invented seam alias failure_journal_export")
    rows = failure_journal.read_failure_journal(tmp_path / "journal.jsonl")
    assert rows
    last = rows[-1]
    assert last["failure_category"] == "seam_contract_mismatch"
    assert last["chosen_remediation_path"] == "semantic_contract_repair"
    assert isinstance(last["autonomy_confidence"], float)
    assert last["continue_autonomously"] is False


def test_task_contract_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    run_task, _, _, _, _, task_contracts, _, _ = _load_runtime_modules()

    def fake_parse(**kwargs):
        assert "task_text" in kwargs
        return {"ALLOWED_METHODS": ["x.y.z run_next_task"]}

    monkeypatch.setattr(task_contracts, "parse_task_contract_directives", fake_parse)
    parsed = run_task.parse_task_contract_directives("## Machine-readable contract directives\n- ALLOWED_METHODS: x.y.z run_next_task\n")
    assert parsed["ALLOWED_METHODS"] == ["x.y.z run_next_task"]


def test_failure_artifact_helper_shared_between_run_task_and_shell_router(monkeypatch, tmp_path, capsys) -> None:
    run_task, _, _, _, _, _, failure_artifacts, shell_router = _load_runtime_modules()
    called = {"count": 0}

    def fake_emit(**kwargs):
        called["count"] += 1
        print(f"emit:{Path(kwargs['last_output_path']).name}:{Path(kwargs['last_bundle_path']).name}")

    monkeypatch.setattr(failure_artifacts, "emit_failure_artifact_messages", fake_emit)

    out_path = tmp_path / "_last_agent_model_output.txt"
    bundle_path = tmp_path / "_last_agent_file_bundle.txt"

    run_task._emit_failure_artifact_messages(out_path, bundle_path, create_placeholders=True, task_file="tasks/x.md")
    shell_router._emit_failure_artifact_messages({}, out_path, bundle_path, task_file="tasks/x.md", failure_category="bundle_transport")

    printed = capsys.readouterr().out
    assert called["count"] == 2
    assert "emit:_last_agent_model_output.txt:_last_agent_file_bundle.txt" in printed


def test_task_scope_heuristic_sets_env_and_recommends_split(monkeypatch, capsys) -> None:
    run_task, _, _, _, _, _, _, _ = _load_runtime_modules()
    # Reset any previous advisory flag and env annotations
    monkeypatch.delenv("TRADINGBOT_SEAM_SPLIT_FAMILIES", raising=False)
    monkeypatch.delenv("TRADINGBOT_SEAM_SPLIT_RECOMMENDATION", raising=False)
    try:
        run_task.__dict__.pop("_SEAM_SPLIT_WARNED_ONCE", None)
    except Exception:
        pass

    required = [
        "docs/ORCHESTRATOR_VISION_AND_CONTROLS.md",
        "agents/lib/shell_router.py",
        "src/builder/orchestrator/runner.py",
    ]
    # Trigger heuristic via partition helper (advisory-only)
    run_task._partition_required_paths_for_normal_bundle(required, [])

    out = capsys.readouterr().out
    # Either the explicit advisory or the lower-level heuristic message should appear
    assert ("Task scope heuristic" in out) or ("Recommendation: split this task" in out)

    families = os.getenv("TRADINGBOT_SEAM_SPLIT_FAMILIES", "")
    assert families is not None
    # Expect at least these seam families to be recognized
    assert "docs" in families
    assert ("orchestrator_core" in families) or ("bootstrap_config" in families)
    assert ("shell_router" in families) or ("meta" in families)

    recommendation = os.getenv("TRADINGBOT_SEAM_SPLIT_RECOMMENDATION", "")
    # Recommendation may be empty if the heuristic routed via shell path later;
    # if present, ensure it contains a split suggestion
    if recommendation:
        assert "split" in recommendation


def test_shell_router_partition_recommends_split(capsys) -> None:
    _, _, _, _, _, _, _, shell_router = _load_runtime_modules()
    required = [
        "docs/ORCHESTRATOR_VISION_AND_CONTROLS.md",
        "agents/run_task.py",
        "agents/lib/failure_journal.py",
    ]
    shell_router._partition_required_paths_for_normal_bundle(required, [])
    out = capsys.readouterr().out
    assert "Recommendation: split this task into focused subtasks." in out


def test_extracted_protected_lane_partition_is_used_by_both_runtimes(monkeypatch) -> None:
    run_task, *_ = _load_runtime_modules()
    shell_router = importlib.import_module("agents.lib.shell_router")
    protected_lane = importlib.import_module("agents.lib.protected_lane")

    calls: dict[str, int] = {"count": 0}

    def fake_partition(required_paths, protected_targets=None, **kwargs):
        calls["count"] += 1
        # Verify that meta harness set is plumbed when provided (optional)
        _ = kwargs.get("protected_meta_paths") or kwargs.get("protected_meta_harness_paths")
        required_paths = [p.replace("\\", "/") for p in required_paths]
        normal = [p for p in required_paths if not p.endswith(".py")]
        protected = [p for p in required_paths if p.endswith(".py")]
        return normal, protected

    monkeypatch.setattr(protected_lane, "partition_required_paths_for_normal_bundle", fake_partition)

    req = ["docs/guide.md", "agents/run_task.py", "src/builder/orchestrator/runner.py"]
    # Both wrappers should delegate to the extracted helper
    n1, p1 = run_task._partition_required_paths_for_normal_bundle(req, [])
    n2, p2 = shell_router._partition_required_paths_for_normal_bundle(req, [])
    assert calls["count"] >= 2
    assert n1 == ["docs/guide.md"] and all(x.endswith(".py") for x in p1)
    assert n2 == ["docs/guide.md"] and all(x.endswith(".py") for x in p2)


def test_bundle_repair_duplicate_classification_preserves_equivalent_and_conflicts() -> None:
    bundle_repair = importlib.import_module("agents.lib.bundle_repair")

    entries = [
        ("a.py", "x = 1\n"),
        ("a.py", "x = 1\r\n"),  # same after newline normalization
        ("b.txt", "hello\n"),
        ("b.txt", "hello world\n"),  # conflict with previous
        ("c.md", "doc\n"),
    ]

    def nn(s: str) -> str:
        return s.replace("\r\n", "\n")

    normalized, conflicts, equivalent = bundle_repair.classify_duplicate_file_entries(entries, normalize_newlines=nn)

    assert normalized["a.py"] == "x = 1\n"
    assert "b.txt" in conflicts and len(conflicts["b.txt"]) == 2
    assert "a.py" in equivalent
    assert "c.md" in normalized and "c.md" not in equivalent and "c.md" not in conflicts


def test_controller_and_extracted_partition_results_match_for_simple_inputs() -> None:
    run_task, *_ = _load_runtime_modules()
    protected_lane = importlib.import_module("agents.lib.protected_lane")

    required = [
        "agents/lib/shell_router.py",
        "src/builder/orchestrator/runner.py",
        "docs/plan.md",
    ]
    # Compare results between controller wrapper and extracted helper for parity
    n_ctrl, p_ctrl = run_task._partition_required_paths_for_normal_bundle(required, [])
    n_ext, p_ext = protected_lane.partition_required_paths_for_normal_bundle(required, [])
    assert set(n_ctrl) == set(n_ext)
    assert set(p_ctrl) == set(p_ext)
