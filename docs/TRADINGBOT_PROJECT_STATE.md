# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–167 are complete in bounded supervised scope:** the repo now freezes public/tested compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes malformed and empty bundle failures, preserves last-known-good subsets during retries, maintains bounded autonomous one-task execution, adds benchmark scorecard integration, improves authority-gate evidence handling, hardens deliverable contracts and completion prompts, normalizes runtime artifact hygiene, completes a second one-task reliability minipack re-proof, moves benchmark decisions onto a strict no-manual-intervention scorecard, and records explicit hosted-authority corroboration state at benchmark time.

The current bounded slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. a bounded autonomous one-task lane with scheduler bridging, explicit stop or requeue policy, supervised handoff, resume-state artifacts, and operator proof bundles
9. strict scorecard and re-proof artifacts that still keep the project in one-task reliability mode rather than broad autonomy mode
10. promotion and widening decisions sourced from a durable, strict scorecard that invalidates any run with manual edits

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- safe-lane autonomy only for one allowlisted safe task at a time under supervision
- operator-readable proof for the bounded one-task lane, not broad autonomy

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, arbitrary multi-task autonomous execution, or broad self-hosting control-plane autonomy.

## Current continuation target

The project should remain in **one-task reliability mode**.

The next tranche should focus on:

1. a strict no-manual-intervention scorecard
2. better authority corroboration and run truth
3. elimination of the dominant remaining one-task failure family
4. a formal promotion re-proof for the one-task lane
5. only then, a gated decision on whether eligible one-task work should become the default orchestrator path and whether a bounded two-task pilot is justified

## Reliability sprint checkpoint

Tasks 157–165 improved the one-task lane materially, but the second minipack re-proof still supports another reliability sprint instead of immediate widening.

## Promotion and widening decision policy

- Promotion and widening decisions are based on the strict benchmark scorecard artifacts written per-session:
  - scorecard.json: durable strict counts (total runs, direct, self-healed, failed, supervised/escalated, authority-blocked, invalidated-by-human).
  - scoreboard.json: legacy-compatible pass-rate surface retained for continuity.
- Any human edit during a run invalidates the run for autonomous success accounting. Only untouched direct or self-healed completions contribute to promotion pass rate.

## Benchmark-time authority corroboration model

To reduce hosted-authority ambiguity noise without weakening conservative discipline, the benchmark/re-proof artifacts now persist an explicit corroboration basis sourced from the hosted-authority and required-check truth surfaces:

- corroboration states recorded:
  - likely_cli_timing_artifact: hosted checks not yet reported (e.g., transient GH CLI settle window); retry is suggested, not success.
  - unresolved_authority_ambiguity: insufficient or conflicting evidence; bounded retry only.
  - confirmed_authority_block: explicit policy block or required-check failure; hard block.
- persisted fields (when applicable):
  - authority_corroboration: {state, category, decision, note, evidence, ok, step}
  - batch_checkpoint.authority_corroboration_state (and mirrored authority_* fields)
- conservative runtime posture:
  - All ambiguity/timing-artifact cases are recorded but do not count as authority success and do not unlock widening.
  - Only confirmed hosted-authority satisfaction combined with local validation can mark a run as eligible to widen.

This corroboration state is derived using enriched helpers in the authority-gate module and wired through the runner’s failure/re-proof artifact writer. The strict scorecard remains the source of truth for promotion/widening eligibility.

## Repository map
[src]
src/builder/orchestrator/__init__.py
src/builder/orchestrator/approval.py
src/builder/orchestrator/audit.py
src/builder/orchestrator/backlog.py
src/builder/orchestrator/backlog_state.py
src/builder/orchestrator/benchmark.py
src/builder/orchestrator/benchmark_scorecard.py
src/builder/orchestrator/ci_manager.py
src/builder/orchestrator/cli.py
src/builder/orchestrator/command_runner.py
src/builder/orchestrator/execution_result.py
src/builder/orchestrator/failures.py
src/builder/orchestrator/git_guardrails.py
src/builder/orchestrator/merge.py
src/builder/orchestrator/orchestrator_runtime.py
src/builder/orchestrator/policy.py
src/builder/orchestrator/pr_manager.py
src/builder/orchestrator/project_adapter.py
src/builder/orchestrator/project_config.py
src/builder/orchestrator/recovery.py
src/builder/orchestrator/repair.py
src/builder/orchestrator/review.py
src/builder/orchestrator/runner.py
src/builder/orchestrator/state.py
src/tradingbot/__init__.py
src/tradingbot/brokers/__init__.py
src/tradingbot/brokers/alpaca.py
src/tradingbot/brokers/base.py
src/tradingbot/config/__init__.py
src/tradingbot/config/settings.py
src/tradingbot/cycle/runner.py
src/tradingbot/data/alpaca_client.py
src/tradingbot/data/cache.py
src/tradingbot/data/client.py
src/tradingbot/data/types.py
src/tradingbot/execution/engine.py
src/tradingbot/execution/types.py
src/tradingbot/indicators.py
src/tradingbot/llm/__init__.py
src/tradingbot/llm/advisor.py
src/tradingbot/llm/noop.py
src/tradingbot/llm/types.py
src/tradingbot/logging/audit.py
src/tradingbot/paper/run_paper_cycle.py
src/tradingbot/planner/intent_planner.py
src/tradingbot/planner/sizing.py
src/tradingbot/portfolio/loader.py
src/tradingbot/portfolio/types.py
src/tradingbot/risk/risk_gate.py
src/tradingbot/risk/types.py
src/tradingbot/run.py
src/tradingbot/runtime/__init__.py
src/tradingbot/strategy/strategy_v1.py
src/tradingbot/strategy/types.py
src/tradingbot/utils/__init__.py
src/tradingbot/utils/market_hours.py
src/tradingbot.egg-info/dependency_links.txt
src/tradingbot.egg-info/PKG-INFO
src/tradingbot.egg-info/SOURCES.txt
src/tradingbot.egg-info/top_level.txt

[tests]
tests/conftest.py
tests/fixtures/sample_app/project_config.json
tests/fixtures/sample_app/tasks/001_sample_task.md
tests/test_alpaca_broker.py
tests/test_artifact_quarantine.py
tests/test_assertion_repair_targeting.py
tests/test_authority_gate.py
tests/test_authority_gate_runtime_integration.py
tests/test_benchmark_live_scorecard_integration.py
tests/test_benchmark_scorecard_integration.py
tests/test_bundle_transport_error_artifacts.py
tests/test_claim_discipline.py
tests/test_completion_integrity.py
tests/test_controller_contract.py
tests/test_cycle_runner_smoke.py
tests/test_execution_engine.py
tests/test_execution_mode_frozen_task.py
tests/test_failure_classifier.py
tests/test_failure_journal.py
tests/test_indicators.py
tests/test_intent_planner.py
tests/test_last_green_subset_preservation.py
tests/test_llm_noop.py
tests/test_market_hours_guard.py
tests/test_merge_manager.py
tests/test_merge_manager_integration.py
tests/test_multi_project_adapters.py
tests/test_orchestrator_approval_flow.py
tests/test_orchestrator_audit.py
tests/test_orchestrator_backlog.py
tests/test_orchestrator_command_runner.py
tests/test_orchestrator_dry_run.py
tests/test_orchestrator_end_to_end.py
tests/test_orchestrator_execute_workflow.py
tests/test_orchestrator_execution_result.py
tests/test_orchestrator_full_simulation.py
tests/test_orchestrator_full_simulation_over_backlog.py
tests/test_orchestrator_git_guardrails.py
tests/test_orchestrator_integrated_capabilities.py
tests/test_orchestrator_package_surface.py
tests/test_orchestrator_persistent_backlog_state.py
tests/test_orchestrator_policy.py
tests/test_orchestrator_pr_creation_workflow.py
tests/test_orchestrator_public_surface.py
tests/test_orchestrator_real_execution.py
tests/test_orchestrator_real_review_gate.py
tests/test_orchestrator_recovery.py
tests/test_orchestrator_resume_after_approval.py
tests/test_orchestrator_run_loop_cli.py
tests/test_orchestrator_run_loop_engine.py
tests/test_orchestrator_runner.py
tests/test_portfolio_loader.py
tests/test_project_adapter.py
tests/test_project_bootstrap_adapter.py
tests/test_project_registry.py
tests/test_public_compat_contract.py
tests/test_real_pr_required_check_smoke_proof.py
tests/test_repair_workflow.py
tests/test_review_checker.py
tests/test_risk_gate.py
tests/test_run_paper_cycle.py
tests/test_run_task_contract_directives.py
tests/test_run_task_parsers_and_policies.py
tests/test_run_task_protected_api_semantic_preflight.py
tests/test_run_task_protected_method_edit_engine.py
tests/test_run_task_runtime_foundations.py
tests/test_run_task_semantic_preflight_parity.py
tests/test_run_task_shell_convergence.py
tests/test_run_task_shell_parity.py
tests/test_runtime_artifact_quarantine.py
tests/test_safe_lint_preflight.py
tests/test_safe_parallelism.py
tests/test_schema_alias_normalization.py
tests/test_second_project_portability.py
tests/test_shell_router_parse_failure_artifacts.py
tests/test_single_task_runner.py
tests/test_smoke.py
tests/test_spec_mode_capture.py
tests/test_stop_vocabulary.py
tests/test_strategy_v1.py
tests/test_task_contracts.py
tests/test_task_eval_corpus.py
tests/test_task_queue.py
tests/test_validator_plugins.py
END_FILE
FILE: agents/lib/final_acceptance.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from agents.lib.controller_contract import AcceptanceDecision, coerce_acceptance_decision, coerce_post_task_decision
from agents.lib.controller_repair import build_controller_repair_context, choose_repair_strategy

AcceptanceFailureClass = Literal[
    "missing_required_in_head",
    "required_only_in_worktree",
    "unexpected_tracked_artifact",
    "merge_ready_validation_failed",
]
CANONICAL_ROOT_DOC_FILES = {"README.md"}
CANONICAL_NARRATIVE_DOC_PREFIXES = ("ORCHESTRATOR_", "TRADINGBOT_")


def canonical_docs_path_for(path: str) -> str:
    normalized = str(path or "").strip().replace("\\", "/")
    if not normalized.endswith(".md"):
        return normalized
    if "/" in normalized:
        return normalized
    if normalized in CANONICAL_ROOT_DOC_FILES:
        return normalized
    filename = Path(normalized).name
    if filename.startswith(CANONICAL_NARRATIVE_DOC_PREFIXES):
        return f"docs/{filename}"
    return normalized


def normalize_paths(paths: Sequence[str] | None) -> list[str]:
    """
    Normalize and filter path-like tokens defensively.

    - Converts slashes and trims whitespace
    - Canonicalizes narrative docs at repo root
    - Drops tokens that do not look like repo file paths (e.g., branch names like 'main')
      by requiring at least a '/' or a '.' in the token.
    """
    out: list[str] = []
    seen: set[str] = set()
    for raw in paths or ():
        path = str(raw or "").strip().replace("\\", "/")
        if not path:
            continue
        # Filter out obvious non-path tokens (e.g., 'main' from mocked git output)
        if "/" not in path and "." not in path:
            continue
        canonical = canonical_docs_path_for(path)
        if canonical not in seen:
            out.append(canonical)
            seen.add(canonical)
    return out


def classify_branch_diff_paths(
    branch_diff_paths: Sequence[str] | None,
    required_paths: Sequence[str] | None,
) -> dict[str, list[str]]:
    required = set(normalize_paths(required_paths))
    diff = normalize_paths(branch_diff_paths)
    required_present: list[str] = []
    unexpected: list[str] = []
    for path in diff:
        if path in required:
            required_present.append(path)
        else:
            unexpected.append(path)
    missing_required = sorted(path for path in required if path not in required_present)
    return {
        "required_present": required_present,
        "missing_required": missing_required,
        "unexpected": unexpected,
    }


def committed_state_parity_issues(
    *,
    validated_required_paths: Sequence[str] | None,
    head_diff_paths: Sequence[str] | None,
    working_tree_paths: Sequence[str] | None,
    strict_required_worktree_only: bool = True,
) -> list[str]:
    issues: list[str] = []
    required = set(normalize_paths(validated_required_paths))
    head = set(normalize_paths(head_diff_paths))
    worktree = set(normalize_paths(working_tree_paths))
    missing_in_head = sorted(path for path in required if path not in head)
    if missing_in_head:
        issues.append("Required deliverables are not present in committed HEAD diff: " + ", ".join(missing_in_head))
    if strict_required_worktree_only:
        worktree_only_required = sorted(path for path in required if path in worktree and path not in head)
        if worktree_only_required:
            issues.append(
                "Required deliverables exist only in working tree (validated but uncommitted): " + ", ".join(worktree_only_required)
            )
    unexpected_head = sorted(path for path in head if path not in required)
    if unexpected_head:
        issues.append(
            "Unexpected paths found in committed HEAD diff (outside validated required paths): " + ", ".join(unexpected_head)
        )
    return issues


def classify_final_acceptance_failure(report: Mapping[str, Any]) -> dict[str, object]:
    decision = str(report.get("acceptance_decision") or "")
    note = str(report.get("note") or "")
    failure_class: AcceptanceFailureClass = "merge_ready_validation_failed"
    if decision != "accepted":
        for token, klass in (
            ("missing_required_in_head", "missing_required_in_head"),
            ("required_only_in_worktree", "required_only_in_worktree"),
            ("unexpected_tracked_artifact", "unexpected_tracked_artifact"),
        ):
            if token in note:
                failure_class = klass  # type: ignore[assignment]
                break
    return {
        "decision": decision or "retryable_failure",
        "failure_class": failure_class,
        "note": note,
    }


def build_final_acceptance_report(
    *,
    task_file: str,
    required_paths: list[str],
    head_diff_paths: list[str],
    working_tree_paths: list[str],
    validation_profile: Mapping[str, Any],
    unexpected_tracked_artifact_findings: list[str] | None = None,
    manual_patch_required: bool = False,
) -> dict[str, object]:
    """
    Build a conservative acceptance report from validation truth and diff signals.
    """
    required_paths = list(required_paths or [])
    head_diff_paths = list(head_diff_paths or [])
    working_tree_paths = list(working_tree_paths or [])
    unexpected_tracked_artifact_findings = list(unexpected_tracked_artifact_findings or [])

    # Default acceptance to the validation result; diff-issues can downgrade.
    passed = bool(validation_profile.get("passed", False))
    decision: AcceptanceDecision = "accepted" if passed else "retryable_failure"
    note_parts: list[str] = []

    parity = classify_branch_diff_paths(head_diff_paths, required_paths)
    parity_issues = committed_state_parity_issues(
        validated_required_paths=required_paths,
        head_diff_paths=head_diff_paths,
        working_tree_paths=working_tree_paths,
        strict_required_worktree_only=True,
    )
    if parity_issues:
        note_parts.extend(parity_issues)
        decision = "retryable_failure"

    if unexpected_tracked_artifact_findings:
        note_parts.append("Unexpected tracked artifact(s): " + ", ".join(sorted(unexpected_tracked_artifact_findings)))
        decision = "retryable_failure"

    if manual_patch_required:
        decision = "manual_patch"  # delegated lane handoff

    return {
        "task_file": str(task_file or ""),
        "validated_required_paths": list(required_paths),
        "head_diff_paths": list(head_diff_paths),
        "working_tree_paths": list(working_tree_paths),
        "parity": parity,
        "acceptance_decision": decision,
        "note": "; ".join(note_parts).strip(),
        "validation_profile": dict(validation_profile),
    }


def build_acceptance_self_heal_context(report: Mapping[str, Any]) -> dict[str, object]:
    route = choose_repair_strategy(
        kind="final_acceptance",
        message=str(report.get("note") or ""),
        category="final_acceptance",
        touched_files=list(report.get("head_diff_paths") or ()),
        task_file=str(report.get("task_file") or ""),
    )
    return build_controller_repair_context(
        kind="final_acceptance",
        message=str(report.get("note") or ""),
        category="final_acceptance",
        touched_files=list(report.get("head_diff_paths") or ()),
        task_file=str(report.get("task_file") or ""),
    ) | {"repair_route": route}


def build_final_acceptance_failure_feedback(report: Mapping[str, Any]) -> str:
    decision = classify_final_acceptance_failure(report)
    note = str(decision.get("note") or "")
    if not note:
        if str(decision.get("decision") or "") != "accepted":
            return "Final acceptance failed for unspecified reasons."
        return "Final acceptance passed."
    return f"Final acceptance failed: {note}"


def report_final_acceptance_failure(report: Mapping[str, Any]) -> None:
    text = build_final_acceptance_failure_feedback(report)
    if text.strip():
        print(text)


def build_final_acceptance_retry_feedback(report: Mapping[str, Any]) -> dict[str, object]:
    decision = classify_final_acceptance_failure(report)
    issues_text = build_final_acceptance_failure_feedback(report)
    should_stop = bool(str(decision.get("decision") or "") == "manual_patch")
    return {
        "acceptance_decision": str(decision.get("decision") or "retryable_failure"),
        "issues_text": issues_text,
        "feedback_text": issues_text,
        "should_stop": should_stop,
    }
