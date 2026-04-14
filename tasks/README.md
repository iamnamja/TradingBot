# Tasks README

## Current execution order for the bounded supervised two-task pilot operation tranche

Use this order after Task 175:

1. `tasks/176_orchestrator_bounded_two_task_pilot_runner_and_pair_ledger.md`
2. `tasks/177_orchestrator_curated_adjacent_pair_corpus_and_admission_manifest.md`
3. `tasks/178_orchestrator_supervised_intervention_artifact_and_pilot_failure_digest.md`
4. `tasks/179_orchestrator_real_bounded_two_task_corpus_benchmark.md`
5. `tasks/180_orchestrator_bounded_two_task_corpus_reproof_and_widening_checkpoint.md`

## Important note

Do **not** widen straight from Task 175 into broad multi-task autonomy or standalone-product work.

The next tranche is specifically about operationalizing the already-approved bounded supervised two-task pilot, gathering real pair-level evidence, and keeping supervision truth explicit.

## Standard numbered-task run command

Use:

`py -m agents.run_task <task-file> --push --keep-runtime-artifacts --provider openai --model gpt-5`

## Branch hygiene reminder

- Keep branch diffs narrow.
- Do not ship runtime scratch artifacts.
- If `_last_subset_preservation.json` appears in a branch diff, restore it from `origin/main` so it drops out of the change set.
