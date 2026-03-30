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
        "_infer_protected_method_targets_from_required": run_task._infer_protected_method_targets_from_required,
        "_task_baseline_paths": lambda required, harness, targets: list(dict.fromkeys(list(required) + [str(t["path"]) for t in targets])),
        "_choose_agent_branch": lambda stem, push: f"agent-{stem}",
        "capture": lambda cmd: "main",
        "ensure_branch": lambda branch: None,
        "existing_file_contents": lambda paths: {path: "def placeholder():\n    pass\n" for path in paths},
        "build_method_insertion_messages": lambda *args, **kwargs: [{"role": "user", "content": "method"}],
        "request_and_parse_method_insertion": lambda messages, model, provider, last_output_path, expected_path, expected_method_name: f"def {expected_method_name}(...):\n    return None\n",
        "apply_method_insertion": lambda content, anchor, method_name, method_text: content,
        "apply_method_replacement": lambda content, method_name, method_text: content + f"\n# replaced {method_name}\n",
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
    assert captured["forbidden_paths"] == ["agents/run_task.py", "agents/lib/shell_router.py"]
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


def test_infer_protected_method_targets_from_required_uses_deterministic_profiles() -> None:
    run_task, _, _, _, _ = _load_runtime_modules()

    inferred = run_task._infer_protected_method_targets_from_required(
        "task",
        ["agents/run_task.py", "agents/lib/shell_router.py"],
    )

    assert {target["path"] for target in inferred} == {"agents/run_task.py", "agents/lib/shell_router.py"}
    assert {target["method_name"] for target in inferred if target["path"] == "agents/run_task.py"} == {
        "_partition_required_paths_for_normal_bundle",
        "_emit_failure_artifact_messages",
    }
    assert "route_shell_main" in {target["method_name"] for target in inferred if target["path"] == "agents/lib/shell_router.py"}


def test_protected_only_task_enters_protected_execution_lane(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    shell_router = importlib.import_module("agents.lib.shell_router")
    monkeypatch.chdir(tmp_path)
    task_path = tmp_path / "protected_only_task.md"
    task_path.write_text("task", encoding="utf-8")

    inserted: list[tuple[str, str, str]] = []

    def fake_request_and_parse_method_insertion(messages, model, provider, last_output_path, expected_path, expected_method_name):
        inserted.append((expected_path, expected_method_name, provider))
        return f"def {expected_method_name}(...):\n    return None\n"

    shell_globals = {
        "_bootstrap_exports": lambda: {},
        "_spec_mode_exports": lambda: {},
        "ensure_clean_worktree": lambda: None,
        "parse_required_files": lambda _text: ["agents/run_task.py", "agents/lib/shell_router.py"],
        "task_requires_material_update": lambda _text: False,
        "task_allows_unchanged_cli": lambda _text: False,
        "parse_harness_file_policies": lambda _text: {},
        "_extract_protected_method_targets": lambda _text: [],
        "_infer_protected_method_targets_from_required": run_task._infer_protected_method_targets_from_required,
        "_task_baseline_paths": lambda required, harness, targets: list(required),
        "_choose_agent_branch": lambda stem, push: f"agent-{stem}",
        "capture": lambda cmd: "main",
        "ensure_branch": lambda branch: None,
        "existing_file_contents": lambda paths: {path: "def placeholder():\n    pass\n" for path in paths},
        "build_method_insertion_messages": lambda *a, **k: [{"role": "user", "content": "method"}],
        "request_and_parse_method_insertion": fake_request_and_parse_method_insertion,
        "apply_method_insertion": lambda content, anchor, method_name, method_text: content,
        "apply_method_replacement": lambda content, method_name, method_text: content + f"\n# replaced {method_name}\n",
        "FileBundleError": run_task.FileBundleError,
        "_report_failure": lambda kind, msg: None,
        "_emit_failure_artifact_messages": run_task._emit_failure_artifact_messages,
        "validate_python_syntax": lambda files: (True, ""),
        "enforce_required_files": lambda *args, **kwargs: (True, ""),
        "enforce_harness_file_policies": lambda *args, **kwargs: (True, ""),
        "validate_static_bundle_contracts": lambda *args, **kwargs: (True, ""),
        "validate_imports": lambda *args, **kwargs: (True, ""),
        "snapshot_file_contents": lambda paths: {},
        "write_files": lambda files: None,
        "run_checks": lambda: (True, ""),
        "_runtime_artifact_paths": lambda *a: [],
        "_cleanup_runtime_artifacts_for_commit": lambda *a, **k: None,
        "run": lambda *a, **k: None,
        "FILE_BUNDLE_BEGIN": "BEGIN_FILE_BUNDLE",
        "FILE_END": "END_FILE",
        "FILE_BUNDLE_END": "END_FILE_BUNDLE",
    }

    args = SimpleNamespace(bootstrap_project="", task=str(task_path), spec_mode=False, push=False, model="m", provider="openai", max_iters=1, policy_block_limit=1)
    result = shell_router.route_shell_main(args, shell_globals)

    assert result == 0
    assert inserted
    assert {path for path, _, _ in inserted} == {"agents/run_task.py", "agents/lib/shell_router.py"}


def test_mixed_task_reconciles_protected_and_normal_lane_results(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    shell_router = importlib.import_module("agents.lib.shell_router")
    monkeypatch.chdir(tmp_path)
    task_path = tmp_path / "mixed_task.md"
    task_path.write_text("task", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_request_and_parse_method_insertion(messages, model, provider, last_output_path, expected_path, expected_method_name):
        return f"def {expected_method_name}(...):\n    return None\n"

    def fake_request_bundle(messages, model, provider, last_output_path, **kwargs):
        captured["expected_paths"] = kwargs.get("expected_paths")
        captured["forbidden_paths"] = kwargs.get("forbidden_paths")
        return {"tests/test_run_task_runtime_foundations.py": "def repaired():\n    return 1\n"}

    shell_globals = {
        "_bootstrap_exports": lambda: {},
        "_spec_mode_exports": lambda: {},
        "ensure_clean_worktree": lambda: None,
        "parse_required_files": lambda _text: ["agents/run_task.py", "tests/test_run_task_runtime_foundations.py"],
        "task_requires_material_update": lambda _text: False,
        "task_allows_unchanged_cli": lambda _text: False,
        "parse_harness_file_policies": lambda _text: {},
        "_extract_protected_method_targets": lambda _text: [],
        "_infer_protected_method_targets_from_required": run_task._infer_protected_method_targets_from_required,
        "_task_baseline_paths": lambda required, harness, targets: list(dict.fromkeys(list(required) + [str(t["path"]) for t in targets])),
        "_choose_agent_branch": lambda stem, push: f"agent-{stem}",
        "capture": lambda cmd: "main",
        "ensure_branch": lambda branch: None,
        "existing_file_contents": lambda paths: {path: "def placeholder():\n    pass\n" for path in paths},
        "build_method_insertion_messages": lambda *a, **k: [{"role": "user", "content": "method"}],
        "request_and_parse_method_insertion": fake_request_and_parse_method_insertion,
        "apply_method_insertion": lambda content, anchor, method_name, method_text: content,
        "apply_method_replacement": lambda content, method_name, method_text: content + f"\n# replaced {method_name}\n",
        "build_messages": lambda *a, **k: [{"role": "user", "content": "bundle"}],
        "request_and_parse_bundle": fake_request_bundle,
        "FileBundleError": run_task.FileBundleError,
        "_report_failure": lambda kind, msg: None,
        "_emit_failure_artifact_messages": run_task._emit_failure_artifact_messages,
        "validate_python_syntax": lambda files: (True, ""),
        "enforce_required_files": lambda required, files, baseline, **kwargs: (set(required).issubset(set(files)), "Missing") ,
        "enforce_harness_file_policies": lambda *args, **kwargs: (True, ""),
        "validate_static_bundle_contracts": lambda *args, **kwargs: (True, ""),
        "validate_imports": lambda *args, **kwargs: (True, ""),
        "snapshot_file_contents": lambda paths: {},
        "write_files": lambda files: captured.setdefault("written", dict(files)),
        "run_checks": lambda: (True, ""),
        "_runtime_artifact_paths": lambda *a: [],
        "_cleanup_runtime_artifacts_for_commit": lambda *a, **k: None,
        "run": lambda *a, **k: None,
        "FILE_BUNDLE_BEGIN": "BEGIN_FILE_BUNDLE",
        "FILE_END": "END_FILE",
        "FILE_BUNDLE_END": "END_FILE_BUNDLE",
    }

    args = SimpleNamespace(bootstrap_project="", task=str(task_path), spec_mode=False, push=False, model="m", provider="openai", max_iters=1, policy_block_limit=1)
    result = shell_router.route_shell_main(args, shell_globals)

    assert result == 0
    assert captured["expected_paths"] == ["tests/test_run_task_runtime_foundations.py"]
    assert captured["forbidden_paths"] == ["agents/run_task.py"]
    written = captured["written"]
    assert "agents/run_task.py" in written
    assert "tests/test_run_task_runtime_foundations.py" in written



def test_equivalent_duplicate_file_entries_are_normalized_safely(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    last_output = tmp_path / "last_output.txt"

    bundle = (
        f"{run_task.FILE_BUNDLE_BEGIN}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 1\n"
        f"{run_task.FILE_END}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 1\n"
        f"{run_task.FILE_END}\n"
        f"{run_task.FILE_BUNDLE_END}\n"
    )

    monkeypatch.setattr(run_task, "chat", lambda messages, model, provider=None: bundle)
    parsed = run_task.request_and_parse_bundle(
        [{"role": "user", "content": "x"}],
        model="m",
        provider="openai",
        last_output_path=last_output,
        expected_paths=["tests/test_run_task_runtime_foundations.py"],
    )

    assert parsed == {"tests/test_run_task_runtime_foundations.py": "def repaired():\n    return 1\n"}
    assert not (tmp_path / "last_output_duplicate_bundle_conflict.json").exists()



def test_conflicting_duplicate_entries_trigger_focused_repair_and_preserve_accepted_files(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    last_output = tmp_path / "last_output.txt"

    first_bundle = (
        f"{run_task.FILE_BUNDLE_BEGIN}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 1\n"
        f"{run_task.FILE_END}\n"
        "FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md\n"
        "# retained doc\n"
        f"{run_task.FILE_END}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 2\n"
        f"{run_task.FILE_END}\n"
        f"{run_task.FILE_BUNDLE_END}\n"
    )
    second_bundle = (
        f"{run_task.FILE_BUNDLE_BEGIN}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 3\n"
        f"{run_task.FILE_END}\n"
        f"{run_task.FILE_BUNDLE_END}\n"
    )
    prompts: list[str] = []
    responses = [first_bundle, second_bundle]

    def fake_chat(messages, model, provider=None):
        prompts.append(messages[-1]["content"])
        return responses.pop(0)

    monkeypatch.setattr(run_task, "chat", fake_chat)
    parsed = run_task.request_and_parse_bundle(
        [{"role": "user", "content": "x"}],
        model="m",
        provider="openai",
        last_output_path=last_output,
        expected_paths=[
            "tests/test_run_task_runtime_foundations.py",
            "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md",
        ],
    )

    assert parsed["tests/test_run_task_runtime_foundations.py"] == "def repaired():\n    return 3\n"
    assert parsed["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"] == "# retained doc\n"
    assert any("Already accepted non-conflicted files:" in prompt for prompt in prompts)
    assert any("docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md" in prompt for prompt in prompts)
    assert not (tmp_path / "last_output_duplicate_bundle_conflict.json").exists()



def test_unresolved_duplicate_conflict_writes_durable_artifact(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    last_output = tmp_path / "last_output.txt"

    first_bundle = (
        f"{run_task.FILE_BUNDLE_BEGIN}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 1\n"
        f"{run_task.FILE_END}\n"
        "FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md\n"
        "# retained doc\n"
        f"{run_task.FILE_END}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 2\n"
        f"{run_task.FILE_END}\n"
        f"{run_task.FILE_BUNDLE_END}\n"
    )
    second_bundle = (
        f"{run_task.FILE_BUNDLE_BEGIN}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 3\n"
        f"{run_task.FILE_END}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 4\n"
        f"{run_task.FILE_END}\n"
        f"{run_task.FILE_BUNDLE_END}\n"
    )
    responses = [first_bundle, second_bundle]
    monkeypatch.setattr(run_task, "chat", lambda messages, model, provider=None: responses.pop(0))
    monkeypatch.chdir(tmp_path)

    try:
        run_task.request_and_parse_bundle(
            [{"role": "user", "content": "x"}],
            model="m",
            provider="openai",
            last_output_path=last_output,
            expected_paths=[
                "tests/test_run_task_runtime_foundations.py",
                "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md",
            ],
        )
    except run_task.FileBundleError as exc:
        assert "Duplicate bundle conflict unresolved after focused repair" in str(exc)
    else:
        raise AssertionError("expected duplicate bundle conflict failure")

    artifact_path = tmp_path / "last_output_duplicate_bundle_conflict.json"
    assert artifact_path.exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "duplicate_bundle_conflict"
    assert payload["conflicted_paths"] == ["tests/test_run_task_runtime_foundations.py"]
    assert payload["accepted_non_conflicted_files"] == ["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"]
    assert payload["focused_repair_attempted"] is True



def test_non_duplicate_malformed_bundle_keeps_current_retry_behavior(tmp_path, monkeypatch) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    last_output = tmp_path / "last_output.txt"

    first_output = "not a bundle at all\n"
    second_output = (
        f"{run_task.FILE_BUNDLE_BEGIN}\n"
        "FILE: tests/test_run_task_runtime_foundations.py\n"
        "def repaired():\n    return 5\n"
        f"{run_task.FILE_END}\n"
        f"{run_task.FILE_BUNDLE_END}\n"
    )
    prompts: list[str] = []
    responses = [first_output, second_output]

    def fake_chat(messages, model, provider=None):
        prompts.append(messages[-1]["content"])
        return responses.pop(0)

    monkeypatch.setattr(run_task, "chat", fake_chat)
    parsed = run_task.request_and_parse_bundle(
        [{"role": "user", "content": "x"}],
        model="m",
        provider="openai",
        last_output_path=last_output,
        expected_paths=["tests/test_run_task_runtime_foundations.py"],
    )

    assert parsed == {"tests/test_run_task_runtime_foundations.py": "def repaired():\n    return 5\n"}
    assert any("Your previous response was INVALID." in prompt for prompt in prompts[1:])
    assert not (tmp_path / "last_output_duplicate_bundle_conflict.json").exists()
