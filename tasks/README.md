# Tasks Index

## Current completed tranche

Tasks 176–180 completed the bounded supervised two-task pilot proof slice:

- 176 — exact two-task pilot runner and pair-level session ledger
- 177 — curated adjacent-pair corpus and admission manifest
- 178 — supervised intervention artifact and pilot failure digest
- 179 — real bounded two-task corpus benchmark
- 180 — bounded two-task corpus re-proof and widening checkpoint

## Current next tranche

The next tranche is reliability first, capability next.

### 181–185 reliability-first tranche

- `tasks/181_orchestrator_failure_family_taxonomy_and_repair_target_selection.md`
- `tasks/182_orchestrator_import_contract_and_additive_compatibility_guardrails.md`
- `tasks/183_orchestrator_resume_checkpoint_and_attempt_state_reentry.md`
- `tasks/184_orchestrator_reliability_benchmark_and_regression_matrix.md`
- `tasks/185_orchestrator_reliability_checkpoint_and_capability_resume_gate.md`

## Standard run command

Use this command for numbered orchestrator tasks:

`py -m agents.run_task <task-file> --push --keep-runtime-artifacts --provider openai --model gpt-5`

## Working rules

- Review merged-main snapshots first.
- Prefer narrow fixes.
- Preserve branch cleanliness.
- Do not ship runtime scratch artifacts.
- If `_last_subset_preservation.json` appears in a branch diff and is tracked, restore it from `origin/main`.
- For proof or re-proof tasks, include an exact `Create or update these exact files` section before attempting execution.
