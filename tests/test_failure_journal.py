from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _bootstrap_repo_root() -> None:
    repo_root = _repo_root()
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _load_failure_journal_module():
    _bootstrap_repo_root()
    if "agents.lib.failure_journal" in sys.modules:
        del sys.modules["agents.lib.failure_journal"]
    return importlib.import_module("agents.lib.failure_journal")


def _load_run_task_module():
    _bootstrap_repo_root()
    if "agents.run_task" in sys.modules:
        del sys.modules["agents.run_task"]
    return importlib.import_module("agents.run_task")

def test_failure_journal_live_seam_exports_are_stable_and_do_not_require_module_alias() -> None:
    run_task = _load_run_task_module()
    exports = run_task._failure_journal_exports()

    expected_keys = {
        "failure_journal",
        "classify_failure",
        "failure_fingerprint",
        "bounded_failure_snippet",
        "recommended_next_action",
        "chosen_remediation_path",
        "append_failure_journal_entry",
        "retry_count_for_fingerprint",
        "build_failure_remediation_plan",
        "autonomy_confidence",
        "continue_autonomously",
        "choose_repair_strategy",
        "build_repair_attempt_record",
        "repair_attempt_fingerprint",
        "evaluate_repair_attempt_memory",
    }

    assert expected_keys.issubset(exports.keys())
    assert "module" not in exports
    assert exports["failure_journal"] is not None
    assert callable(exports["append_failure_journal_entry"])
    assert callable(exports["build_failure_remediation_plan"])



def test_repeated_failures_are_fingerprinted_and_counted() -> None:
    fj = _load_failure_journal_module()
    fp1 = fj.failure_fingerprint(kind="imports", message="NameError: name 'x1' is not defined", category="imports")
    fp2 = fj.failure_fingerprint(kind="imports", message="NameError: name 'x2' is not defined", category="imports")
    assert fp1 == fp2

    fj._FAILURE_COUNTS.clear()
    assert fj.retry_count_for_fingerprint(fp1) == 1
    assert fj.retry_count_for_fingerprint(fp1) == 2


def test_raw_failure_snippet_is_bounded_and_transport_safe_in_test_source() -> None:
    fj = _load_failure_journal_module()
    marker_text = (
        "prefix\n"
        + "BEGIN_" + "FILE_BUNDLE\n"
        + "FI" + "LE: x.py\n"
        + "END_" + "FILE\n"
        + "END_" + "FILE_BUNDLE\n"
    ) * 40
    bounded = fj.bounded_failure_snippet(marker_text, max_chars=120)
    assert len(bounded) <= 120
    assert "BEGIN_" + "FILE_BUNDLE" in bounded
    assert "FI" + "LE:" in bounded


def test_report_failure_delegates_through_live_export_seam(monkeypatch) -> None:
    run_task = _load_run_task_module()
    monkeypatch.setattr(run_task, "_FAILURE_JOURNAL_STATE", {}, raising=False)

    calls = {"classify": 0, "append": 0}
    entries = []

    def classify(kind, message):
        calls["classify"] += 1
        return "classified"

    def fingerprint(*, kind, message, category):
        assert category == "classified"
        return "fp-1"

    def bounded(message, max_chars=400):
        return "snippet"

    def recommend(*, kind, message, category, retry_count, fingerprint, raw_failure_snippet):
        return "retry_with_targeted_fix"

    def choose(*, kind, message, category, retry_count, fingerprint, raw_failure_snippet, recommended_next_action):
        return "retry_with_targeted_fix"

    def append(entry):
        calls["append"] += 1
        entries.append(entry)

    monkeypatch.setattr(
        run_task,
        "_failure_journal_exports",
        lambda: {
            "classify_failure": classify,
            "failure_fingerprint": fingerprint,
            "bounded_failure_snippet": bounded,
            "recommended_next_action": recommend,
            "chosen_remediation_path": choose,
            "append_failure_journal_entry": append,
            "retry_count_for_fingerprint": lambda fingerprint: 2,
        },
    )

    run_task._report_failure("imports", "boom")
    assert calls == {"classify": 1, "append": 1}
    assert entries[0]["failure_category"] == "classified"
    assert entries[0]["retry_count"] == 2
    assert entries[0]["recommended_next_action"] == "retry_with_targeted_fix"
    assert entries[0]["chosen_remediation_path"] == "retry_with_targeted_fix"


def test_report_failure_appends_journal_rows_with_recommended_and_chosen_paths(monkeypatch, tmp_path: Path) -> None:
    journal_path = tmp_path / "failure_journal.jsonl"
    monkeypatch.setenv("TRADINGBOT_FAILURE_JOURNAL_PATH", str(journal_path))
    monkeypatch.setenv("TRADINGBOT_TASK_ID", "task-045")

    run_task = _load_run_task_module()
    monkeypatch.setattr(run_task, "_FAILURE_JOURNAL_STATE", {}, raising=False)
    cache = getattr(run_task._failure_journal_exports, "_cache", None)
    if isinstance(cache, dict):
        cache.clear()
        delattr(run_task._failure_journal_exports, "_cache")

    run_task._report_failure("imports", "NameError: name 'x1' is not defined")
    run_task._report_failure("imports", "NameError: name 'x2' is not defined")

    fj = _load_failure_journal_module()
    rows = fj.read_failure_journal(journal_path)
    assert len(rows) == 2
    assert rows[0]["task_id"] == "task-045"
    assert rows[0]["recommended_next_action"]
    assert rows[0]["chosen_remediation_path"]
    assert rows[0]["failure_fingerprint"] == rows[1]["failure_fingerprint"]
    assert rows[0]["retry_count"] == 1
    assert rows[1]["retry_count"] == 2


def test_failure_remediation_plan_uses_same_strategy_vocabulary_as_router() -> None:
    fj = _load_failure_journal_module()
    router = fj.choose_repair_strategy(kind="tests", message="pytest failure in test_example", category="tests")
    plan = fj.build_failure_remediation_plan(
        kind="tests",
        message="pytest failure in test_example",
        category="tests",
        retry_count=1,
        fingerprint="fp-1",
        raw_failure_snippet="pytest failure in test_example",
    )

    assert plan["repair_strategy"] == router["repair_strategy"]
    assert plan["remediation_lane"] == router["remediation_lane"]
    assert plan["continue_autonomously"] == router["continue_autonomously"]


def test_failure_router_sends_ci_only_failures_to_verifier_lane() -> None:
    fj = _load_failure_journal_module()
    route = fj.choose_repair_strategy(
        kind="ci",
        message="GitHub Actions required check failed",
        category="ci_only_failure",
    )

    assert route["repair_strategy"] == "ci_verification_recheck"
    assert route["remediation_lane"] == "verifier"
    assert route["stop_after_failure"] is False


def test_failure_router_keeps_environment_failures_manual() -> None:
    fj = _load_failure_journal_module()
    route = fj.choose_repair_strategy(
        kind="environment",
        message="pip install failed because the toolchain is missing",
        category="environment_setup_failure",
    )

    assert route["repair_strategy"] == "environment_setup_triage"
    assert route["remediation_lane"] == "operator"
    assert route["stop_after_failure"] is True


def test_collection_failures_are_classified_explicitly_before_generic_imports() -> None:
    fj = _load_failure_journal_module()
    category = fj.classify_failure(
        "tests",
        "ERROR collecting tests/test_multi_project_adapters.py\nImportError while importing test module\ncannot import name 'run_multi_agent_controller_cycle'",
    )

    assert category == "collection_import_failure"


def test_collection_failures_route_to_narrow_builder_repair_lane() -> None:
    fj = _load_failure_journal_module()
    plan = fj.build_failure_remediation_plan(
        kind="tests",
        message="ERROR collecting tests/test_multi_project_adapters.py\nImportError while importing test module\ncannot import name 'run_multi_agent_controller_cycle'",
        category="collection_import_failure",
        retry_count=1,
        fingerprint="fp-collection",
        raw_failure_snippet="ERROR collecting tests/test_multi_project_adapters.py",
    )

    assert plan["repair_strategy"] == "collection_import_contract_repair"
    assert plan["remediation_lane"] == "builder"
    assert plan["continue_autonomously"] is True


def test_report_failure_journals_collection_failure_category_explicitly(monkeypatch, tmp_path: Path) -> None:
    journal_path = tmp_path / "failure_journal.jsonl"
    monkeypatch.setenv("TRADINGBOT_FAILURE_JOURNAL_PATH", str(journal_path))

    run_task = _load_run_task_module()
    monkeypatch.setattr(run_task, "_FAILURE_JOURNAL_STATE", {}, raising=False)
    cache = getattr(run_task._failure_journal_exports, "_cache", None)
    if isinstance(cache, dict):
        cache.clear()
        delattr(run_task._failure_journal_exports, "_cache")

    run_task._report_failure(
        "tests",
        "ERROR collecting tests/test_multi_project_adapters.py\nImportError while importing test module\ncannot import name 'run_multi_agent_controller_cycle'",
    )

    fj = _load_failure_journal_module()
    rows = fj.read_failure_journal(journal_path)
    assert rows[-1]["failure_category"] == "collection_import_failure"
    assert rows[-1]["repair_strategy"] == "collection_import_contract_repair"
    assert rows[-1]["remediation_lane"] == "builder"


def test_targeted_repair_planner_prefers_minimal_compatibility_surface() -> None:
    fj = _load_failure_journal_module()
    plan = fj.build_failure_remediation_plan(
        kind="tests",
        message="ERROR collecting tests/test_multi_project_adapters.py\nImportError while importing test module\ncannot import name 'run_multi_agent_controller_cycle'",
        category="collection_import_failure",
        retry_count=1,
        fingerprint="fp-collection",
        raw_failure_snippet="ERROR collecting tests/test_multi_project_adapters.py",
    )

    assert plan["targeted_patch_surface"] == "compatibility_alias_only"
    assert plan["prefer_minimal_patch"] is True
    assert plan["minimal_patch_selected"] is True
    assert plan["max_files_to_edit"] <= 2


def test_targeted_repair_planner_prefers_docs_only_sync_for_proof_claim_drift() -> None:
    fj = _load_failure_journal_module()
    route = fj.choose_repair_strategy(
        kind="docs",
        message="README proof claim drift against bounded portability status narrative",
        category="docs_proof_claim_drift",
        touched_files=["README.md", "docs/TRADINGBOT_PROJECT_STATE.md"],
    )

    assert route["targeted_patch_surface"] == "docs_claim_sync"
    assert route["prefer_minimal_patch"] is True
    assert route["minimal_patch_selected"] is True
    assert all(str(path).endswith('.md') for path in route["target_files"])


def test_multi_agent_failure_context_persists_role_artifact_summaries() -> None:
    fj = _load_failure_journal_module()

    context = fj.build_multi_agent_failure_context(
        task_path="tasks/108_orchestrator_role_handoff_artifact_envelopes_and_persistence.md",
        role_trace=["controller", "builder", "verifier", "controller"],
        builder_artifact={
            "role": "builder",
            "task_path": "tasks/108_orchestrator_role_handoff_artifact_envelopes_and_persistence.md",
            "summary": "Builder proposed a bounded persistence patch.",
            "attempt_count": 1,
            "changed_files": ["agents/lib/batch_state.py"],
            "proposed_next_role": "verifier",
            "role_outcome": "builder_patch_proposed",
        },
        verifier_artifact={
            "role": "verifier",
            "task_path": "tasks/108_orchestrator_role_handoff_artifact_envelopes_and_persistence.md",
            "summary": "Verifier replayed focused tests and found a failing checkpoint assertion.",
            "focused_results": ["pytest -q tests/test_controller_contract.py"],
            "full_results": ["pytest -q"],
            "verdict": "fail",
            "verification_authority_profile": "local_only",
            "role_outcome": "verification_failed",
        },
        controller_decision={
            "role": "controller",
            "task_path": "tasks/108_orchestrator_role_handoff_artifact_envelopes_and_persistence.md",
            "summary": "Controller requested a narrow persistence repair.",
            "action": "repair",
            "repair_strategy": "targeted_role_persistence_fix",
            "remediation_lane": "builder",
            "next_role_decision": "builder",
            "post_task_decision": "stop",
            "role_outcome": "controller_routed",
        },
    )

    assert context["coder_artifact_summary"]["envelope_type"] == "coder_output"
    assert context["tester_artifact_summary"]["envelope_type"] == "tester_output"
    assert context["controller_artifact_summary"]["envelope_type"] == "controller_output"
    assert context["tester_artifact_summary"]["verifier_verdict"] == "fail"
    assert context["controller_artifact_summary"]["post_task_decision"] == "stop"
    assert context["builder_summary"] == "Builder proposed a bounded persistence patch."


def test_multi_agent_failure_context_includes_tester_critique_summary() -> None:
    fj = _load_failure_journal_module()
    context = fj.build_multi_agent_failure_context(
        task_path="tasks/109_orchestrator_tester_critique_bundle_and_focused_replay_lane.md",
        role_trace=["controller", "builder", "controller", "verifier", "controller"],
        builder_artifact={
            "role": "builder",
            "summary": "builder changed verifier surface",
            "changed_files": ["agents/lib/multi_agent_loop.py"],
        },
        verifier_artifact={
            "role": "verifier",
            "summary": "verification failed",
            "failure_message": "ERROR collecting tests/test_multi_project_adapters.py\nImportError while importing test module\ncannot import name 'run_multi_agent_controller_cycle' from 'agents.lib.multi_agent_loop'",
            "failure_category": "collection_import_failure",
            "focused_results": ["pytest -q tests/test_multi_project_adapters.py"],
            "full_results": ["pytest -q"],
            "tester_critique_bundle": {
                "likely_failure_family": "import_contract",
                "critique_summary": "Tester found likely import/contract drift.",
                "focused_replay_commands": ["pytest -q tests/test_multi_project_adapters.py"],
                "broad_replay_commands": ["pytest -q"],
                "likely_touched_files": ["agents/lib/multi_agent_loop.py"],
                "failing_test_files": ["tests/test_multi_project_adapters.py"],
            },
        },
        controller_decision={
            "summary": "controller requested targeted repair",
            "action": "repair",
            "repair_strategy": "collection_import_contract_repair",
            "remediation_lane": "builder",
        },
    )

    assert context["tester_critique_summary"]["likely_failure_family"] == "import_contract"
    assert context["focused_replay_commands"] == ["pytest -q tests/test_multi_project_adapters.py"]
    assert context["likely_touched_files"] == ["agents/lib/multi_agent_loop.py"]


def test_repair_attempt_memory_detects_duplicate_no_progress_plan() -> None:
    fj = _load_failure_journal_module()
    attempt1 = fj.build_repair_attempt_record(
        task_path="tasks/110.md",
        repair_strategy="behavioral_test_repair",
        targeted_patch_surface="result_shape_adapter",
        target_files=["agents/lib/multi_agent_loop.py"],
        failure_fingerprint="fp-1",
        retry_count=1,
    )
    attempt2 = fj.build_repair_attempt_record(
        task_path="tasks/110.md",
        repair_strategy="behavioral_test_repair",
        targeted_patch_surface="result_shape_adapter",
        target_files=["agents/lib/multi_agent_loop.py"],
        failure_fingerprint="fp-1",
        retry_count=2,
    )

    memory = fj.evaluate_repair_attempt_memory(current_attempt=attempt2, prior_attempts=[attempt1], retry_budget=2)

    assert memory["duplicate_attempt_suppressed"] is True
    assert memory["no_progress_detected"] is True
    assert memory["repair_memory_signal"] == "duplicate_no_progress_repair_plan"


def test_failure_remediation_plan_persists_repair_attempt_surface_metadata() -> None:
    fj = _load_failure_journal_module()
    plan = fj.build_failure_remediation_plan(
        kind="tests",
        message="pytest failure in test_example",
        category="tests",
        retry_count=1,
        fingerprint="fp-1",
        raw_failure_snippet="pytest failure in test_example",
    )

    assert plan["repair_attempt_fingerprint"].startswith("repair:")
    assert plan["repair_target_surface"] == plan["targeted_patch_surface"]
    assert plan["repair_target_files"] == plan["target_files"]


def test_repair_ranking_prefers_minimal_builder_and_rollback_on_regression() -> None:
    fj = _load_failure_journal_module()
    last_green = fj.build_validation_snapshot(lint_ok=True, test_ok=True, branch_clean=True, required_checks_passed=True)
    current = fj.build_validation_snapshot(lint_ok=True, test_ok=False, branch_clean=True, required_checks_passed=True)

    ranked = fj.rank_repair_candidates(
        [
            {
                "repair_strategy": "behavioral_test_repair",
                "remediation_lane": "builder",
                "target_files": ["agents/lib/a.py"],
                "minimal_patch_selected": True,
            },
            {
                "repair_strategy": "manual_stop",
                "remediation_lane": "operator",
                "target_files": [],
                "manual_lane_recommended": True,
            },
        ],
        current_validation_snapshot=current,
        last_green_snapshot=last_green,
    )

    rollback = fj.evaluate_rollback_to_last_green(
        current_validation_snapshot=current,
        last_green_snapshot=last_green,
    )

    assert ranked[0]["repair_strategy"] == "behavioral_test_repair"
    assert ranked[0]["repair_rank"] == 1
    assert rollback["regressed_from_last_green"] is True
    assert rollback["should_rollback_to_last_green"] is True
