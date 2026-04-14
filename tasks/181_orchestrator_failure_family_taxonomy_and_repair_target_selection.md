# Task 181 — orchestrator failure family taxonomy and repair target selection

## Why

Recent task runs show that the orchestrator can sometimes repair the wrong layer, spend retries on compatibility drift rather than the actual task goal, or recover broadly when a narrower repair target would have been sufficient.

The repo now needs an explicit failure-family taxonomy and a narrower repair-target selection surface.

## Scope

Define durable failure-family classification and use it to choose narrower repair targets.

## Runtime seams to reuse

- Reuse current task-admission and exact deliverable-contract enforcement.
- Reuse current subset-preservation and rollback truth where available.
- Reuse existing static-contract and protected-surface checks.
- Reuse bounded one-task and bounded two-task run artifacts as evidence of recurring failure families.

## Requirements

- Introduce a durable taxonomy for recurring orchestrator failure families, including at minimum:
  - task admission / missing exact deliverable contract
  - import / public compatibility surface failure
  - artifact path or artifact shape mismatch
  - benchmark compatibility regression
  - static contract / protected surface violation
  - resume or environment re-entry mismatch
- Persist classification truth in a way later repair logic can reuse.
- Add or harden repair-target selection so these families map to narrower default repair surfaces.
- Keep the behavior conservative:
  - classification should reduce broad repair attempts, not encourage them,
  - protected surfaces and one-task truth surfaces remain respected.

## Create or update these exact files

- `agents/lib/repair_targeting.py`
- `tests/test_repair_targeting.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/181_orchestrator_failure_family_taxonomy_and_repair_target_selection.md`

## Non-goals

- Do not redesign the full orchestrator planner.
- Do not widen capability claims.
- Do not bypass proof-task admission or protected-surface checks.

## Acceptance criteria

- There is an explicit failure-family taxonomy for the recurring orchestrator failures this project has seen recently.
- Repair-target selection maps those families to narrower repair surfaces.
- Tests cover at least one narrow target-selection expectation per major failure family.
- Docs describe the reliability-first reason for this step without overclaiming broader autonomy.

## Implementation notes

- Prefer additive classification and mapping helpers over broad runtime rewrites.
- It is acceptable to default ambiguous failures to a conservative generic family, but the specific families above must be represented explicitly.
- Artifact shape: persisted classification records are small JSON files tagged with a stable short code per family to make dashboards/readouts deterministic.

## Deliverable pointers

- Code and mapping helpers: `agents/lib/repair_targeting.py`
- Tests: `tests/test_repair_targeting.py`
- Narrative updates: `README.md`, `docs/README.md`, and `docs/TRADINGBOT_PROJECT_STATE.md`

## Outcome

After this task, the orchestrator has:

- an explicit and durable taxonomy for failure-family classification,
- persisted classification truth suitable for later repair logic,
- narrower default repair-target selection per family,
- and a conservative behavior profile that reduces broad repair attempts while preserving protected and one-task proof surfaces.

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
tests/fixtures/bounded_two_task_pairs.json
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
tests/test_run_task_contracts.py
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
