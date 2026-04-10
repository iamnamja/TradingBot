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


def _load_task_eval_corpus_module():
    _bootstrap_repo_root()
    if "agents.lib.task_eval_corpus" in sys.modules:
        del sys.modules["agents.lib.task_eval_corpus"]
    return importlib.import_module("agents.lib.task_eval_corpus")

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
        "build_external_safe_pass_rate_scoreboard",
        "write_external_safe_pass_rate_scoreboard",
        "build_external_safe_failure_digest",
        "write_external_safe_failure_digest",
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



def test_failure_journal_supports_bounded_portfolio_repair_tracking() -> None:
    fj = _load_failure_journal_module()
    plan = fj.build_failure_remediation_plan(
        kind="validation",
        message="project A failed checks",
        retry_count=1,
        max_repair_attempts=2,
    )
    assert plan["bounded"] is True
    assert plan["max_repair_attempts"] == 2


def test_bundle_failure_classification_and_remediation_plans_are_distinct() -> None:
    fj = _load_failure_journal_module()

    assert fj.classify_failure("bundle_transport", "Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.") == "bundle_markerless_transport"
    assert fj.classify_failure("bundle_transport", "Missing FILE blocks from the requested scope: tests/test_x.py") == "bundle_underfilled_response"
    assert fj.classify_failure("bundle_transport", "No FILE: blocks could be parsed (check FILE:/END_FILE lines).") == "bundle_malformed_transport"

    empty_plan = fj.build_failure_remediation_plan(
        kind="bundle_empty_response",
        message="Bundle transport was present but contained zero FILE blocks.",
        retry_count=1,
        max_repair_attempts=3,
    )
    underfilled_plan = fj.build_failure_remediation_plan(
        kind="bundle_underfilled_response",
        message="Missing FILE blocks from the requested scope: tests/test_x.py",
        retry_count=1,
        max_repair_attempts=3,
    )
    markerless_plan = fj.build_failure_remediation_plan(
        kind="bundle_markerless_transport",
        message="Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.",
        retry_count=1,
        max_repair_attempts=3,
    )

    assert empty_plan["repair_strategy"] == "bundle_empty_response_retry"
    assert underfilled_plan["repair_strategy"] == "missing_deliverable_retry"
    assert markerless_plan["repair_strategy"] == "bundle_transport_format_retry"
    assert underfilled_plan["targeted_patch_surface"] == "bundle_missing_deliverables"
    assert markerless_plan["targeted_patch_surface"] == "bundle_transport_format"


def test_task_136_failure_corpus_reproof_remains_bounded_and_distinct() -> None:
    fj = _load_failure_journal_module()

    empty_plan = fj.build_failure_remediation_plan(
        kind="bundle_empty_response",
        message="Bundle transport was present but contained zero FILE blocks.",
        retry_count=1,
        max_repair_attempts=3,
    )
    underfilled_plan = fj.build_failure_remediation_plan(
        kind="bundle_underfilled_response",
        message="Missing FILE blocks from the requested scope: docs/TRADINGBOT_PROJECT_STATE.md",
        retry_count=1,
        max_repair_attempts=3,
    )
    no_ready_plan = fj.build_failure_remediation_plan(
        kind="portfolio_scheduler",
        message="no dependency-ready task available",
        retry_count=1,
        max_repair_attempts=3,
    )

    assert empty_plan["bounded"] is True
    assert underfilled_plan["bounded"] is True
    assert no_ready_plan["bounded"] is True
    assert empty_plan["repair_strategy"] == "bundle_empty_response_retry"
    assert underfilled_plan["repair_strategy"] == "missing_deliverable_retry"
    assert no_ready_plan["repair_strategy"] == "manual_stop"
    assert no_ready_plan["continue_autonomously"] is False


def test_build_autonomous_single_task_recovery_report_aggregates_stop_reasons_and_hosted_authority() -> None:
    fj = _load_failure_journal_module()
    report = fj.build_autonomous_single_task_recovery_report(
        entries=[
            {
                "final_decision": "completed",
                "escalation": {"required": False, "reason": ""},
                "validation": {"no_checks_reported_observed": True},
            },
            {
                "final_decision": "execution_failed",
                "escalation": {"required": True, "reason": "Admitted single-task run failed and should be handed back to supervised recovery."},
                "validation": {"no_checks_reported_observed": False},
            },
            {
                "final_decision": "escalation_required",
                "escalation": {"required": True, "reason": "Task touches self-hosting control-plane or harness surfaces and must be escalated for supervised/manual handling."},
                "validation": {"no_checks_reported_observed": False},
            },
        ],
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        generated_at="2026-04-08T18:00:00Z",
    )

    assert report["total_runs"] == 3
    assert report["handoff_required_count"] == 2
    assert report["recovery_required_count"] == 1
    assert report["escalation_required_count"] == 2
    assert report["hosted_authority_blocked_runs"] == 1
    assert report["hosted_authority_blocking_frequency"] == 0.3333
    assert report["stop_reason_counts"]["completed"] == 1
    assert report["stop_reason_counts"]["execution_failed"] == 1
    assert report["stop_reason_counts"]["escalation_required"] == 1
    assert len(report["escalation_reason_counts"]) == 2



def test_write_autonomous_single_task_recovery_report_persists_json_artifact(tmp_path: Path) -> None:
    fj = _load_failure_journal_module()
    target = tmp_path / "artifacts" / "autonomous_single_task" / "recovery_report.json"
    report = {
        "schema_version": 1,
        "report_type": "autonomous_single_task_recovery_report",
        "total_runs": 2,
    }

    written = fj.write_autonomous_single_task_recovery_report(report, report_path=target)

    assert Path(written) == target
    assert target.exists()
    loaded = target.read_text(encoding="utf-8")
    assert '"total_runs": 2' in loaded



def test_task_142_safe_lane_reproof_recovery_report_remains_bounded_to_one_task_handoffs() -> None:
    fj = _load_failure_journal_module()
    report = fj.build_autonomous_single_task_recovery_report(
        entries=[
            {
                "final_decision": "completed",
                "escalation": {"required": False, "reason": ""},
                "validation": {"no_checks_reported_observed": False},
            },
            {
                "final_decision": "blocked_supervised_only",
                "escalation": {"required": False, "reason": "Task remains supervised because it is proof shaped."},
                "validation": {"no_checks_reported_observed": False},
            },
            {
                "final_decision": "escalation_required",
                "escalation": {
                    "required": True,
                    "reason": "Task touches self-hosting control-plane or harness surfaces and must be escalated for supervised/manual handling.",
                },
                "validation": {"no_checks_reported_observed": True},
            },
        ],
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        generated_at="2026-04-08T18:45:00Z",
    )

    assert report["total_runs"] == 3
    assert report["handoff_required_count"] == 2
    assert report["recovery_required_count"] == 0
    assert report["escalation_required_count"] == 1
    assert report["blocked_supervised_only_count"] == 1
    assert report["hosted_authority_blocked_runs"] == 1
    assert report["stop_reason_counts"]["completed"] == 1
    assert report["stop_reason_counts"]["blocked_supervised_only"] == 1
    assert report["stop_reason_counts"]["escalation_required"] == 1



def test_recovery_report_counts_resumed_reentry_and_completed_entry_reuse() -> None:
    fj = _load_failure_journal_module()
    report = fj.build_autonomous_single_task_recovery_report(
        entries=[
            {
                "final_decision": "completed",
                "escalation": {"required": False, "reason": ""},
                "validation": {"no_checks_reported_observed": False},
                "resume": {"resume_reentry": True, "reused_completed_entry": False},
            },
            {
                "final_decision": "completed",
                "escalation": {"required": False, "reason": ""},
                "validation": {"no_checks_reported_observed": False},
                "resume": {"resume_reentry": False, "reused_completed_entry": True},
            },
        ],
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        generated_at="2026-04-09T20:15:00Z",
    )

    assert report["resumed_reentry_count"] == 1
    assert report["reused_completed_entry_count"] == 1



def test_task_148_live_canary_operator_bundle_recovery_report_shows_one_success_and_one_explicit_handoff() -> None:
    fj = _load_failure_journal_module()
    report = fj.build_autonomous_single_task_recovery_report(
        entries=[
            {
                "final_decision": "completed",
                "escalation": {"required": False, "reason": ""},
                "validation": {"no_checks_reported_observed": False},
            },
            {
                "final_decision": "escalation_required",
                "escalation": {
                    "required": True,
                    "reason": "Task touches self-hosting control-plane or harness surfaces and must be escalated for supervised/manual handling.",
                },
                "validation": {"no_checks_reported_observed": False},
            },
        ],
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        generated_at="2026-04-09T22:20:00Z",
    )

    assert report["total_runs"] == 2
    assert report["handoff_required_count"] == 1
    assert report["recovery_required_count"] == 0
    assert report["escalation_required_count"] == 1
    assert report["blocked_supervised_only_count"] == 0
    assert report["stop_reason_counts"]["completed"] == 1
    assert report["stop_reason_counts"]["escalation_required"] == 1


def test_build_external_safe_pass_rate_scoreboard_summarizes_completion_self_heal_and_authority() -> None:
    fj = _load_failure_journal_module()
    scoreboard = fj.build_external_safe_pass_rate_scoreboard(
        entries=[
            {
                "admission": {
                    "autonomous_single_task_allowed": True,
                    "proof_task_admission_allowed": True,
                },
                "retry": {"retry_count_observed": 0},
                "validation": {"no_checks_reported_observed": False},
                "multi_agent_loop": {"repair_artifact": {"repair_required": False, "repair_attempt_selected": False}},
                "final_decision": "completed",
            },
            {
                "admission": {
                    "autonomous_single_task_allowed": True,
                    "proof_task_admission_allowed": True,
                },
                "retry": {"retry_count_observed": 1},
                "validation": {"no_checks_reported_observed": True},
                "multi_agent_loop": {"repair_artifact": {"repair_required": True, "repair_attempt_selected": True}},
                "final_decision": "completed",
            },
            {
                "admission": {
                    "autonomous_single_task_allowed": True,
                    "proof_task_admission_allowed": True,
                },
                "retry": {"retry_count_observed": 1},
                "validation": {"no_checks_reported_observed": False},
                "multi_agent_loop": {"repair_artifact": {"repair_required": True, "repair_attempt_selected": True}},
                "final_decision": "execution_failed",
            },
            {
                "admission": {
                    "autonomous_single_task_allowed": False,
                    "proof_task_admission_allowed": True,
                },
                "retry": {"retry_count_observed": 0},
                "validation": {"no_checks_reported_observed": False},
                "multi_agent_loop": {"repair_artifact": {"repair_required": False, "repair_attempt_selected": False}},
                "final_decision": "blocked_supervised_only",
            },
        ],
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        generated_at="2026-04-10T14:30:00Z",
    )

    assert scoreboard["total_runs"] == 4
    assert scoreboard["admitted_runs"] == 3
    assert scoreboard["completed_runs"] == 2
    assert scoreboard["completed_without_manual_help_runs"] == 1
    assert scoreboard["completed_after_self_heal_runs"] == 1
    assert scoreboard["escalated_runs"] == 1
    assert scoreboard["blocked_supervised_only_runs"] == 1
    assert scoreboard["blocked_by_authority_runs"] == 1
    assert scoreboard["pass_rate"] == 0.6667
    assert scoreboard["self_heal_success_rate"] == 0.5
    assert scoreboard["next_reproof_target"]["target_metric"] == "pass_rate"


def test_build_external_safe_failure_digest_summarizes_dominant_non_completion_reasons() -> None:
    fj = _load_failure_journal_module()
    digest = fj.build_external_safe_failure_digest(
        entries=[
            {
                "final_decision": "execution_failed",
                "validation": {"no_checks_reported_observed": False},
                "multi_agent_loop": {"failure_taxonomy": {"failure_family": "lint_only_failure", "failure_category": "lint"}},
            },
            {
                "final_decision": "execution_failed",
                "validation": {"no_checks_reported_observed": False},
                "multi_agent_loop": {"failure_taxonomy": {"failure_family": "lint_only_failure", "failure_category": "lint"}},
            },
            {
                "final_decision": "blocked_supervised_only",
                "admission": {"proof_task_admission_reason": "Task remains outside the bounded allowlisted safe lane."},
                "validation": {"no_checks_reported_observed": False},
            },
            {
                "final_decision": "escalation_required",
                "validation": {"no_checks_reported_observed": True},
                "escalation": {"reason": "Task touches self-hosting control-plane or harness surfaces and must be escalated."},
            },
        ],
        journal_entries=[
            {"failure_category": "lint"},
            {"failure_category": "lint"},
            {"failure_category": "import_contract"},
        ],
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        journal_path="artifacts/failure_journal.jsonl",
        generated_at="2026-04-10T14:31:00Z",
    )

    assert digest["non_completion_runs"] == 4
    assert digest["dominant_non_completion_reasons"][0]["reason"] == "lint_only_failure"
    assert digest["dominant_non_completion_reasons"][0]["count"] == 2
    assert digest["dominant_failure_families"][0]["failure_family"] == "lint"
    assert digest["failure_family_counts"]["lint"] == 2
    assert digest["failure_family_counts"]["import_contract"] == 1


def test_write_external_safe_scoreboard_and_failure_digest_persist_json_artifacts(tmp_path: Path) -> None:
    fj = _load_failure_journal_module()
    scoreboard_target = tmp_path / "artifacts" / "autonomous_single_task" / "pass_rate_scoreboard.json"
    digest_target = tmp_path / "artifacts" / "autonomous_single_task" / "failure_digest.json"

    scoreboard_written = fj.write_external_safe_pass_rate_scoreboard(
        {"schema_version": 1, "artifact_type": "external_safe_one_task_pass_rate_scoreboard", "completed_runs": 3},
        scoreboard_path=scoreboard_target,
    )
    digest_written = fj.write_external_safe_failure_digest(
        {"schema_version": 1, "artifact_type": "external_safe_one_task_failure_digest", "non_completion_runs": 2},
        digest_path=digest_target,
    )

    assert Path(scoreboard_written) == scoreboard_target
    assert Path(digest_written) == digest_target
    assert '"completed_runs": 3' in scoreboard_target.read_text(encoding="utf-8")
    assert '"non_completion_runs": 2' in digest_target.read_text(encoding="utf-8")


def test_task_153_external_safe_corpus_reproof_supports_a_meaningful_supervised_pass_rate_band() -> None:
    fj = _load_failure_journal_module()
    corpus = _load_task_eval_corpus_module()
    manifest = corpus.external_safe_eval_manifest_snapshot()

    entries = [
        {
            "admission": {"autonomous_single_task_allowed": True, "proof_task_admission_allowed": True},
            "retry": {"retry_count_observed": 0},
            "validation": {"no_checks_reported_observed": False},
            "multi_agent_loop": {"repair_artifact": {"repair_required": False, "repair_attempt_selected": False}},
            "final_decision": "completed",
        },
        {
            "admission": {"autonomous_single_task_allowed": True, "proof_task_admission_allowed": True},
            "retry": {"retry_count_observed": 1},
            "validation": {"no_checks_reported_observed": False},
            "multi_agent_loop": {"repair_artifact": {"repair_required": True, "repair_attempt_selected": True}},
            "final_decision": "completed",
        },
        {
            "admission": {"autonomous_single_task_allowed": True, "proof_task_admission_allowed": True},
            "retry": {"retry_count_observed": 0},
            "validation": {"no_checks_reported_observed": False},
            "multi_agent_loop": {"repair_artifact": {"repair_required": False, "repair_attempt_selected": False}},
            "final_decision": "completed",
        },
        {
            "admission": {"autonomous_single_task_allowed": True, "proof_task_admission_allowed": True},
            "retry": {"retry_count_observed": 1},
            "validation": {"no_checks_reported_observed": True},
            "multi_agent_loop": {"repair_artifact": {"repair_required": True, "repair_attempt_selected": True}},
            "final_decision": "completed",
        },
        {
            "admission": {"autonomous_single_task_allowed": True, "proof_task_admission_allowed": True},
            "retry": {"retry_count_observed": 1},
            "validation": {"no_checks_reported_observed": False},
            "multi_agent_loop": {
                "repair_artifact": {"repair_required": True, "repair_attempt_selected": True},
                "failure_taxonomy": {"failure_family": "formatting_lint_only", "failure_category": "lint"},
            },
            "final_decision": "execution_failed",
        },
        {
            "admission": {"autonomous_single_task_allowed": True, "proof_task_admission_allowed": True},
            "retry": {"retry_count_observed": 0},
            "validation": {"no_checks_reported_observed": True},
            "multi_agent_loop": {"repair_artifact": {"repair_required": False, "repair_attempt_selected": False}},
            "final_decision": "execution_failed",
        },
    ]

    scoreboard = fj.build_external_safe_pass_rate_scoreboard(
        entries=entries,
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        generated_at="2026-04-10T15:10:00Z",
    )
    digest = fj.build_external_safe_failure_digest(
        entries=entries,
        journal_entries=[{"failure_category": "lint"}],
        ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl",
        journal_path="artifacts/failure_journal.jsonl",
        generated_at="2026-04-10T15:10:00Z",
    )

    assert manifest["item_count"] == 6
    assert scoreboard["total_runs"] == manifest["item_count"]
    assert scoreboard["pass_rate"] == 0.6667
    assert scoreboard["completed_runs"] > digest["non_completion_runs"]
    assert scoreboard["completed_after_self_heal_runs"] == 2
    assert scoreboard["self_heal_success_rate"] == 0.6667
    assert scoreboard["next_reproof_target"]["minimum_meaningful_band"] == "at_least_0.6_on_external_safe_corpus"
    assert digest["dominant_non_completion_reasons"] == [
        {"reason": "formatting_lint_only", "count": 1},
        {"reason": "hosted_authority_no_checks_reported", "count": 1},
    ]

