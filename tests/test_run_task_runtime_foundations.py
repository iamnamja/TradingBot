from __future__ import annotations

import json
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
    return run_task, check_runner, git_ops, provider_client, failure_journal


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _ = _load_runtime_modules()
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
    run_task, check_runner, _, _, _ = _load_runtime_modules()

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
    run_task, _, _, _, _ = _load_runtime_modules()
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
    _, _, _, _, failure_journal = _load_runtime_modules()
    assert failure_journal.classify_failure("tests", "SyntaxError: invalid syntax in generated test") == "python_syntax"
    assert failure_journal.classify_failure("bundle_transport", "references invented seam alias failure_journal_export") == "seam_contract_mismatch"
    assert failure_journal.classify_failure("policy", "Protected meta file(s) in normal bundle lane") == "harness_meta_regression"


def test_failure_remediation_plans_choose_different_paths() -> None:
    _, _, _, _, failure_journal = _load_runtime_modules()
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
    run_task, _, _, _, failure_journal = _load_runtime_modules()
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



def test_request_and_parse_bundle_preserves_good_file_during_localized_subset_repair(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()

    outputs = iter([
        """BEGIN_FILE_BUNDLE
FILE: tests/test_run_task_runtime_foundations.py
def broken(:
    pass
END_FILE
FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md
# patched doc
END_FILE
END_FILE_BUNDLE""",
        """BEGIN_FILE_BUNDLE
FILE: tests/test_run_task_runtime_foundations.py
def repaired():
    return 1
END_FILE
END_FILE_BUNDLE""",
    ])

    monkeypatch.setattr(run_task, "chat", lambda *a, **k: next(outputs))

    parsed = run_task.request_and_parse_bundle(
        messages=[{"role": "user", "content": "task"}],
        model="m",
        provider="openai",
        last_output_path=tmp_path / "last_output.txt",
        expected_paths=[
            "tests/test_run_task_runtime_foundations.py",
            "docs/ORCHESTRATOR_PRODUCT_SPEC.md",
        ],
        baseline={
            "tests/test_run_task_runtime_foundations.py": "def baseline():\n    return 0\n",
            "docs/ORCHESTRATOR_PRODUCT_SPEC.md": "# baseline doc\n",
        },
    )

    assert parsed["docs/ORCHESTRATOR_PRODUCT_SPEC.md"] == "# patched doc\n"
    assert "def repaired():" in parsed["tests/test_run_task_runtime_foundations.py"]


def test_request_and_parse_bundle_writes_durable_failure_artifact_on_localized_repair_rejection(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()

    outputs = iter([
        """BEGIN_FILE_BUNDLE
FILE: tests/test_run_task_runtime_foundations.py
def broken(:
    pass
END_FILE
FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md
# patched doc
END_FILE
END_FILE_BUNDLE""",
        """BEGIN_FILE_BUNDLE
FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md
# wrong subset
END_FILE
END_FILE_BUNDLE""",
    ])

    monkeypatch.setattr(run_task, "chat", lambda *a, **k: next(outputs))
    last_output = tmp_path / "last_output.txt"

    try:
        run_task.request_and_parse_bundle(
            messages=[{"role": "user", "content": "task"}],
            model="m",
            provider="openai",
            last_output_path=last_output,
            expected_paths=[
                "tests/test_run_task_runtime_foundations.py",
                "docs/ORCHESTRATOR_PRODUCT_SPEC.md",
            ],
            baseline={
                "tests/test_run_task_runtime_foundations.py": "def baseline():\n    return 0\n",
                "docs/ORCHESTRATOR_PRODUCT_SPEC.md": "# baseline doc\n",
            },
        )
    except run_task.FileBundleError as exc:
        assert "Localized repair rejected bad subset" in str(exc)
    else:
        raise AssertionError("expected localized repair rejection")

    artifact_path = tmp_path / "last_output_localized_repair_failure.json"
    assert artifact_path.exists()
    payload = __import__("json").loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "localized_repair_failure"
    assert payload["preserved_paths"] == ["docs/ORCHESTRATOR_PRODUCT_SPEC.md"]
    assert payload["rejected_paths"] == ["tests/test_run_task_runtime_foundations.py"]
    assert payload["rejection_reason"]
    assert ("requested scope" in payload["rejection_reason"] or "No FILE: blocks could be parsed" in payload["rejection_reason"])
    assert "FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md" in payload["localized_repair_raw_output"]




def test_protected_meta_deliverables_are_partitioned_out_of_normal_bundle_scope() -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    normal, protected = run_task._partition_required_paths_for_normal_bundle(
        [
            "agents/run_task.py",
            "tests/test_run_task_runtime_foundations.py",
            "agents/lib/shell_router.py",
        ],
        [],
    )

    assert normal == ["tests/test_run_task_runtime_foundations.py"]
    assert protected == ["agents/run_task.py", "agents/lib/shell_router.py"]


def test_non_protected_deliverables_remain_in_normal_bundle_scope_for_mixed_tasks(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    shell_router = importlib.import_module("agents.lib.shell_router")
    monkeypatch.chdir(tmp_path)
    task_path = tmp_path / "mixed_task.md"
    task_path.write_text("task", encoding="utf-8")

    captured: dict[str, object] = {}
    reports: list[tuple[str, str]] = []

    def fake_request_bundle(messages, model, provider, last_output_path, **kwargs):
        captured["expected_paths"] = kwargs.get("expected_paths")
        captured["forbidden_paths"] = kwargs.get("forbidden_paths")
        last_output_path.write_text("synthetic model output\n", encoding="utf-8")
        return {"tests/test_run_task_runtime_foundations.py": "from __future__ import annotations\n"}

    shell_globals = {
        "_bootstrap_exports": lambda: {},
        "_spec_mode_exports": lambda: {},
        "ensure_clean_worktree": lambda: None,
        "parse_required_files": lambda _text: [
            "agents/run_task.py",
            "agents/lib/shell_router.py",
            "tests/test_run_task_runtime_foundations.py",
        ],
        "task_requires_material_update": lambda _text: False,
        "task_allows_unchanged_cli": lambda _text: False,
        "parse_harness_file_policies": lambda _text: {},
        "_extract_protected_method_targets": lambda _text: [],
        "_task_baseline_paths": lambda required, harness, targets: list(required),
        "_choose_agent_branch": lambda stem, push: f"agent-{stem}",
        "capture": lambda cmd: "main",
        "ensure_branch": lambda branch: None,
        "existing_file_contents": lambda paths: {},
        "build_messages": lambda *args, **kwargs: [{"role": "user", "content": "x"}],
        "request_and_parse_bundle": fake_request_bundle,
        "FILE_BUNDLE_BEGIN": "BEGIN_FILE_BUNDLE",
        "FILE_END": "END_FILE",
        "FILE_BUNDLE_END": "END_FILE_BUNDLE",
        "FileBundleError": run_task.FileBundleError,
        "_report_failure": lambda kind, msg: reports.append((kind, msg)),
        "validate_python_syntax": lambda files: (True, ""),
        "enforce_required_files": lambda *args, **kwargs: (False, "Missing required deliverables (must be created/updated): agents/run_task.py, agents/lib/shell_router.py"),
        "enforce_harness_file_policies": lambda *args, **kwargs: (True, ""),
        "validate_static_bundle_contracts": lambda *args, **kwargs: (True, ""),
        "validate_imports": lambda *args, **kwargs: (True, ""),
        "_append_task_feedback": lambda task_text, message: task_text,
        "_repeat_limit_exceeded": run_task._repeat_limit_exceeded,
        "_emit_failure_artifact_messages": run_task._emit_failure_artifact_messages,
    }

    args = SimpleNamespace(
        bootstrap_project="",
        task=str(task_path),
        spec_mode=False,
        push=False,
        model="m",
        provider="openai",
        max_iters=1,
        policy_block_limit=1,
    )

    result = shell_router.route_shell_main(args, shell_globals)

    assert result == 1
    assert captured["expected_paths"] == ["tests/test_run_task_runtime_foundations.py"]
    assert captured["forbidden_paths"] == ["agents/lib/shell_router.py", "agents/run_task.py"]
    assert reports[-1][0] == "deliverables"


def test_protected_only_task_writes_truthful_placeholder_failure_artifacts(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    shell_router = importlib.import_module("agents.lib.shell_router")
    monkeypatch.chdir(tmp_path)
    task_path = tmp_path / "protected_only_task.md"
    task_path.write_text("task", encoding="utf-8")

    reports: list[tuple[str, str]] = []

    shell_globals = {
        "_bootstrap_exports": lambda: {},
        "_spec_mode_exports": lambda: {},
        "ensure_clean_worktree": lambda: None,
        "parse_required_files": lambda _text: ["agents/run_task.py", "agents/lib/shell_router.py"],
        "task_requires_material_update": lambda _text: False,
        "task_allows_unchanged_cli": lambda _text: False,
        "parse_harness_file_policies": lambda _text: {},
        "_extract_protected_method_targets": lambda _text: [],
        "_task_baseline_paths": lambda required, harness, targets: list(required),
        "_choose_agent_branch": lambda stem, push: f"agent-{stem}",
        "capture": lambda cmd: "main",
        "ensure_branch": lambda branch: None,
        "existing_file_contents": lambda paths: {},
        "FileBundleError": run_task.FileBundleError,
        "_report_failure": lambda kind, msg: reports.append((kind, msg)),
        "_emit_failure_artifact_messages": run_task._emit_failure_artifact_messages,
    }

    args = SimpleNamespace(
        bootstrap_project="",
        task=str(task_path),
        spec_mode=False,
        push=False,
        model="m",
        provider="openai",
        max_iters=1,
        policy_block_limit=1,
    )

    result = shell_router.route_shell_main(args, shell_globals)

    assert result == 1
    assert reports[-1][0] == "bundle_transport"

    model_output = tmp_path / "_last_agent_model_output.txt"
    bundle_output = tmp_path / "_last_agent_file_bundle.txt"
    assert model_output.exists()
    assert bundle_output.exists()

    model_payload = json.loads(model_output.read_text(encoding="utf-8"))
    bundle_payload = json.loads(bundle_output.read_text(encoding="utf-8"))

    assert model_payload["artifact_kind"] == "model_output_placeholder"
    assert bundle_payload["artifact_kind"] == "file_bundle_placeholder"
    assert model_payload["before_model_output"] is True
    assert bundle_payload["before_model_output"] is True
    assert model_payload["protected_files"] == ["agents/run_task.py", "agents/lib/shell_router.py"]


def test_non_protected_tasks_keep_all_required_files_in_normal_bundle_scope() -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    normal, protected = run_task._partition_required_paths_for_normal_bundle(
        [
            "tests/test_run_task_runtime_foundations.py",
            "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md",
        ],
        [],
    )

    assert normal == [
        "tests/test_run_task_runtime_foundations.py",
        "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md",
    ]
    assert protected == []
