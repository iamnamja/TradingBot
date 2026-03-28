# TradingBot — Task Backlog

This repository contains two related products in one codebase:

- **TradingBot** — the application being built
- **Orchestrator** — the reusable software-delivery engine that is building and hardening the project

## Current state

### TradingBot

TradingBot remains at **manual paper-trading readiness**.

### Orchestrator

The orchestrator baseline through **Task 054b** is complete on `main`:

- 031–048 — execution, guardrails, resumability, failure journal, spec mode, bootstrap, plugins, safe parallelism ✅
- 049–052 — shell convergence, public interface freeze, docs normalization, portability proof ✅
- 053 — stable seam registry ✅
- 054a–054b — meta harness lane gate + bundle preflight/localized repair ✅

## Why the trajectory is changing

The continuation originally planned for 055–061 assumed the orchestrator was already reliable enough to execute narrow integration tasks with little supervision.

Recent runs showed a different reality:

- task specs can still drift into the wrong task family
- integration-test generation is still too freeform
- failure handling is better at **blocking** bad output than **recovering** locally
- the orchestrator still lacks a true control plane that can decide readiness, next-task selection, remediation, and when to stay autonomous versus when to escalate

So the next tranche is a **Reliability, Recovery, and Autonomy tranche** before resuming the postponed continuation items.

## Do we need AI on top of the orchestrator?

Not as a separate supervisory product.

What we need is an **embedded controller-intelligence layer inside the orchestrator** that can:

- classify task families
- compile the right prompt/strategy for the lane
- validate seam contracts semantically, not only with string checks
- classify failures into repairable vs escalation-worthy
- preserve good outputs and repair only bad subsets
- decide whether to retry, split, defer, patch the task, patch the harness, or open a manual lane

The orchestrator should remain the control plane. Model-backed reasoning should be a constrained internal capability, not an uncontrolled AI sitting above it.

## New near-term plan

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

### Deferred continuation after reliability tranche

- `062_orchestrator_integrated_capabilities_e2e`
- `063_orchestrator_failure_journal_live_seam`
- `064_orchestrator_safe_parallelism_review_integration`
- `065_orchestrator_runtime_artifact_quarantine_integration`
- `066_orchestrator_package_extraction_prep`
- `067_orchestrator_canonical_docs_path_policy`
- `068_orchestrator_task_scope_and_split_heuristics`

## Current recommendation

Do **not** push more continuation tasks through the existing automation loop until the reliability/recovery/autonomy tranche lands.

The best next move is:

1. freeze the stable harness contract,
2. teach the orchestrator to classify task families and compile the right lane-specific prompt,
3. add a seam manifest + semantic contract validator,
4. add a real failure classifier + localized repair loop,
5. add backlog readiness + PR/CI/merge control, and then
6. resume the deferred continuation items on top of a more reliable controller.
