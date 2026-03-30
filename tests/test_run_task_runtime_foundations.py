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


def test_parse_required_files_only_from_supported_explicit_sections() -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    task_text = """
# Task

Please consider `docs/IGNORED.md` in prose only.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Notes

Mentioning `src/not_required.py` here should not count.
"""
    assert run_task.parse_required_files(task_text) == [
        "agents/run_task.py",
        "tests/test_run_task_runtime_foundations.py",
        "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md",
    ]


def test_parse_required_files_ignores_ambiguous_task_text() -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    task_text = """
# Task

Please improve the runtime. You may need to touch `agents/run_task.py` and
maybe `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`, but this is not an explicit
deliverables section.
"""
    assert run_task.parse_required_files(task_text) == []


def test_attempt_missing_deliverable_repair_requests_only_missing_files_and_preserves_accepted(monkeypatch, tmp_path) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    captured: dict[str, object] = {}

    def fake_build_messages(task_text, required, extra_directives="", virtual_context=None, forbidden_normal_bundle_paths=None):
        captured["required"] = list(required)
        captured["virtual_context"] = dict(virtual_context or {})
        return [{"role": "user", "content": "repair"}]

    def fake_request_and_parse_bundle(messages, model, provider, last_output_path, forbidden_paths=None, expected_paths=None, baseline=None):
        captured["expected_paths"] = list(expected_paths or [])
        return {"docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md": "# repaired doc\n"}

    monkeypatch.setattr(run_task, "build_messages", fake_build_messages)
    monkeypatch.setattr(run_task, "request_and_parse_bundle", fake_request_and_parse_bundle)

    merged = run_task._attempt_missing_deliverable_repair(
        task_text="""
## Create or update these exact files
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
""",
        accepted_files={"tests/test_run_task_runtime_foundations.py": "def ok():\n    return 1\n"},
        missing_paths=["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"],
        model="m",
        provider="openai",
        last_output_path=tmp_path / "last_output.txt",
        baseline={"docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md": "# baseline\n"},
    )

    assert captured["required"] == ["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"]
    assert captured["expected_paths"] == ["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"]
    assert "tests/test_run_task_runtime_foundations.py" in captured["virtual_context"]
    assert merged["tests/test_run_task_runtime_foundations.py"].startswith("def ok():")
    assert merged["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"] == "# repaired doc\n"


def test_enforce_deliverable_completeness_triggers_focused_repair_and_returns_complete_bundle(monkeypatch, tmp_path) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()
    calls: dict[str, object] = {}

    def fake_attempt_missing_deliverable_repair(**kwargs):
        calls["missing_paths"] = list(kwargs["missing_paths"])
        calls["accepted_files"] = dict(kwargs["accepted_files"])
        repaired = dict(kwargs["accepted_files"])
        repaired["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"] = "# repaired\n"
        return repaired

    monkeypatch.setattr(run_task, "_attempt_missing_deliverable_repair", fake_attempt_missing_deliverable_repair)

    ok, merged, message = run_task.enforce_deliverable_completeness(
        task_path=Path("tasks/065a_orchestrator_deliverable_completeness_enforcement.md"),
        task_text="""
## Create or update these exact files

- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
""",
        accepted_files={"tests/test_run_task_runtime_foundations.py": "def ok():\n    return 1\n"},
        model="m",
        provider="openai",
        last_output_path=tmp_path / "last_output.txt",
        baseline={"docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md": "# baseline\n"},
    )

    assert ok is True
    assert message == ""
    assert calls["missing_paths"] == ["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"]
    assert "tests/test_run_task_runtime_foundations.py" in calls["accepted_files"]
    assert merged["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"] == "# repaired\n"


def test_enforce_deliverable_completeness_writes_durable_failure_artifact_when_missing_remains(monkeypatch, tmp_path) -> None:
    run_task, _, _, _, _ = _load_runtime_modules()

    monkeypatch.setattr(
        run_task,
        "_attempt_missing_deliverable_repair",
        lambda **kwargs: dict(kwargs["accepted_files"]),
    )

    ok, merged, message = run_task.enforce_deliverable_completeness(
        task_path=Path("tasks/065a_orchestrator_deliverable_completeness_enforcement.md"),
        task_text="""
## Create or update these exact files

- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
""",
        accepted_files={"tests/test_run_task_runtime_foundations.py": "def ok():\n    return 1\n"},
        model="m",
        provider="openai",
        last_output_path=tmp_path / "last_output.txt",
        baseline={"docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md": "# baseline\n"},
    )

    assert ok is False
    assert "Missing required deliverables after focused repair" in message
    artifact_path = tmp_path / "last_output_deliverable_completeness_failure.json"
    assert artifact_path.exists()
    payload = __import__("json").loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "deliverable_completeness_failure"
    assert payload["task_file"] == "tasks/065a_orchestrator_deliverable_completeness_enforcement.md"
    assert payload["required_deliverables"] == [
        "tests/test_run_task_runtime_foundations.py",
        "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md",
    ]
    assert payload["accepted_files"] == ["tests/test_run_task_runtime_foundations.py"]
    assert payload["missing_deliverables"] == ["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"]
    assert payload["focused_repair_attempted"] is True
    assert merged["tests/test_run_task_runtime_foundations.py"].startswith("def ok():")
