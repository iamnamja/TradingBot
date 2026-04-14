# Task 186 — orchestrator docs status headline consistency guard

## Why

Recent successful tasks still required manual cleanup because the repo’s high-level status headlines drifted across `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md`.

The repo needs an explicit guard so narrative state stops lagging behind code and task progress.

## Scope

Add a durable docs-status consistency guard for the repo’s current-state headlines and tranche references.

## Runtime seams to reuse

- Reuse the existing status narrative in `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md`.
- Reuse current task-order and tranche docs under `tasks/` and `docs/`.
- Reuse the reliability-first discipline of small, additive validation helpers.

## Requirements

- Introduce an explicit check for the current status headline and tranche consistency across the repo’s top-level status docs.
- At minimum, guard:
  - `README.md`
  - `docs/TRADINGBOT_PROJECT_STATE.md`
  - any current tranche/index doc that also carries the active task range or status headline
- Keep the guard deterministic and conservative.
- The guard should fail on drift rather than silently rewriting all docs.
- Add tests that would have caught the manual Task 183 and Task 184 headline mismatches.

## Create or update these exact files

- `agents/lib/docs_status_guard.py`
- `tests/test_docs_status_guard.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/186_orchestrator_docs_status_headline_consistency_guard.md`

## Non-goals

- Do not redesign all project docs.
- Do not auto-edit unrelated narrative sections.
- Do not widen capability claims.

## Acceptance criteria

- A deterministic guard exists for the repo status headlines.
- Tests fail when headline task numbers drift across guarded docs.
- Docs explain that this is a contract-hardening step, not a capability step.

## Implementation notes

- Prefer one narrow parser/validator over broad text rewriting.
- It is acceptable to define a small “current status” source-of-truth shape if that keeps the guard stable.

## Deliverables

- A narrow validator at `agents/lib/docs_status_guard.py` that:
  - extracts the “completed through Task N” headline across `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md`
  - extracts the active tranche range (e.g., `186–190`) across `README.md`, `docs/README.md`, and `docs/TRADINGBOT_PROJECT_STATE.md`
  - fails when numbers drift
  - provides a machine-readable report and a CLI exit code
- Tests at `tests/test_docs_status_guard.py` that:
  - pass on the current repo snapshot
  - fail with simulated mismatches representative of the Task 183/184 cleanup issues
- Short, additive doc notes acknowledging the new guard and its intent as a contract-hardening step.

## Operator notes

- The guard is conservative and deterministic. It raises on drift and produces a small JSON report.
- It does not attempt to rewrite docs. Narrative ownership remains with humans.
- To introduce a new tranche, update the three guarded docs consistently in the same PR to keep the guard green.
- Run locally with `python -m agents.lib.docs_status_guard`. The guard normalizes en-dash vs. hyphen differences for ranges and reports any disagreement paths for quick manual fixes.

## Repository map
[src]
src/builder/orchestrator/__init__.py
src/builder/orchestrator/approval.py
src/builder/orchestrator/audit.py
src/builder/orchestrator/backlog.py
src/builder/orchestrator/backlog_state.py
src/builder/orchestrator/benchmark.py
src/builder/orchestrator/benchmark_scorecard.py
src/builder/orchestrator/bounded_corpus_benchmark.py
src/builder/orchestrator/ci_manager.py
src/builder/orchestrator/cli.py
src/builder/orchestrator/command_runner.py
src/builder/orchestrator/execution_result.py
src/builder/orchestrator/failures.py
src/builder/orchestrator/git_guardrails.py
src/builder/orchestrator/merge.py
src/builder/orchestrator/orchestrator_runtime.py
src/builder/orchestrator/pilot_failure_digest.py
src/builder/orchestrator/policy.py
src/builder/orchestrator/pr_manager.py
src/builder/orchestrator/project_adapter.py
src/builder/orchestrator/recovery.py
src/builder/orchestrator/reliability_benchmark.py
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
tests/fixtures/bounded_two_task_pairs.json
tests/fixtures/sample_app/project_config.json
tests/fixtures/sample_app/tasks/001_sample_task.md
tests/test_alpaca_broker.py
tests/test_artifact_quarantine.py
tests/test_assertion_repair_targeting.py
tests/test_attempt_state_resume.py
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
tests/test_reliability_benchmark.py
tests/test_repair_targeting.py
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
