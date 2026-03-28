# Task 055 — Orchestrator Reliability and Autonomy Umbrella

## Goal

Pause the previously planned continuation and insert a focused reliability / recovery / autonomy tranche that turns the orchestrator from a guarded task runner into a genuine backlog control plane.

## This task is an umbrella

Do **not** run this task directly.

It exists to define the ordered subtask sequence, scope boundaries, and acceptance bar for the reliability/autonomy tranche.

## Ordered subtasks

1. `055a_orchestrator_harness_contract_freeze` *(manual patch lane first)*
2. `055b_orchestrator_task_family_classifier_prompt_compiler_and_split_strategy` *(autonomous lane after 055a lands)*
3. `055c_orchestrator_seam_manifest_and_semantic_contract_validator` *(manual patch lane first)*
4. `056_orchestrator_failure_classifier_and_remediation_planner`
5. `057_orchestrator_localized_repair_and_failure_artifacts`
6. `058_orchestrator_backlog_readiness_and_state_engine`
7. `059_orchestrator_ci_pr_merge_controller`
8. `060_orchestrator_autonomy_loop_integration`
9. `061_orchestrator_continuation_reset_and_numbering_sync`

## Tranche intent

By the end of this tranche, the orchestrator should be materially closer to a system that can:

- decide what task is ready next
- classify task families before generation
- compile the right lane-specific request
- validate seam contracts semantically
- classify failure modes and map them to remediation paths
- keep good files and repair only bad subsets
- manage PR/CI/merge as part of its control loop
- resume the deferred continuation without repeated numbering drift and manual confusion

## Deferred continuation after this umbrella

The previously planned continuation has been renumbered to 062–068 and should resume only after the reliability/autonomy tranche lands.


## Lane note

To bootstrap the tranche safely:

- `055a` should be landed via a **manual patch lane**
- `055c` should be landed via a **manual patch lane**
- `055b` is the first task in this tranche that should go back through the normal autonomous lane after `055a` merges
