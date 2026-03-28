# TradingBot — Task Backlog

This folder is the execution backlog for the TradingBot build and the co-located orchestrator product.

## Current posture

The next priority is **not** broad feature continuation. The next priority is the orchestrator’s **Reliability / Recovery / Autonomy tranche** so the controller can eventually manage long backlogs with much less human steering.

## Near-term task order

### Reliability / Recovery / Autonomy tranche (active)

- `055_orchestrator_reliability_and_autonomy_umbrella` (do not run directly)
- `055a_orchestrator_harness_contract_freeze`
- `055b_orchestrator_task_family_classifier_prompt_compiler_and_split_strategy`
- `055c_orchestrator_seam_manifest_and_semantic_contract_validator`
- `056_orchestrator_failure_classifier_and_remediation_planner`
- `057_orchestrator_localized_repair_and_failure_artifacts`
- `058_orchestrator_backlog_readiness_and_state_engine`
- `059_orchestrator_ci_pr_merge_controller`
- `060_orchestrator_autonomy_loop_integration`
- `061_orchestrator_continuation_reset_and_numbering_sync`

### Deferred continuation (resume after reliability tranche)

- `062_orchestrator_integrated_capabilities_e2e`
- `063_orchestrator_failure_journal_live_seam`
- `064_orchestrator_safe_parallelism_review_integration`
- `065_orchestrator_runtime_artifact_quarantine_integration`
- `066_orchestrator_package_extraction_prep`
- `067_orchestrator_canonical_docs_path_policy`
- `068_orchestrator_task_scope_and_split_heuristics`

## Execution recommendation

For the active tranche:

- treat meta-harness tasks as protected/manual-patch-first where needed
- prefer narrow, deterministic acceptance criteria
- require semantic contract validation for seam-heavy tasks
- prefer localized repair over whole-task restart when a small bundle partially succeeds
- keep docs/roadmap/task numbering synchronized whenever the trajectory changes
