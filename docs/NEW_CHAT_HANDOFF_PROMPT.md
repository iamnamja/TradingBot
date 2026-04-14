We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth. I will upload current `agents.zip`, `docs.zip`, `tasks.zip`, `tests.zip`, and sometimes the root `README.md` from merged `main`.

Current state:

- repo is complete through Task 175,
- the one-task lane is conditionally ready under supervision,
- the bounded supervised two-task pilot is now explicitly ready, but only in bounded supervised scope,
- tasks 171–175 established:
  - two-task pilot admission and eligibility truth,
  - dependency-aware adjacent-task A->B handoff contract,
  - controller-contract compatibility restoration for bounded pilot,
  - supervised dev/test role split for bounded pilot,
  - two-task canary scorecard and benchmark artifacts,
  - bounded two-task pilot re-proof and product checkpoint,
- the project is still **not** claiming broad multi-task autonomy,
- the standalone orchestrator-as-its-own-app phase remains blocked.

Honest posture right now:

- one-task work is the default proving path under supervision,
- bounded supervised two-task pilot work is now ready to be exercised,
- broad multi-task autonomy is still not justified,
- standalone productization remains blocked.

Next planned tranche:

- 176 orchestrator_bounded_two_task_pilot_runner_and_pair_ledger
- 177 orchestrator_curated_adjacent_pair_corpus_and_admission_manifest
- 178 orchestrator_supervised_intervention_artifact_and_pilot_failure_digest
- 179 orchestrator_real_bounded_two_task_corpus_benchmark
- 180 orchestrator_bounded_two_task_corpus_reproof_and_widening_checkpoint

Strategic direction:

- Phase A: one-task truth established enough to serve as the default supervised path.
- Phase B: bounded supervised two-task pilot is now ready and should be exercised conservatively with real curated adjacent-task pairs.
- Phase C: only after durable real two-task corpus evidence should we consider any broader multi-task widening.
- Phase D: standalone orchestrator-app work remains later and blocked behind stronger multi-task proof.

How we’ve been working together:

- First, review the uploaded current-main snapshots before planning anything.
- Then provide a zip patch with updated docs/tasks (and code too if needed).
- After providing the zip, give exact PowerShell commands to:
  1. reset to clean `main`
  2. create a branch
  3. optionally delete stale files before applying the zip
  4. expand/copy the zip into the repo
  5. inspect diffs
  6. run validation
  7. commit/push/create PR/merge
  8. reset back to clean `main`
- When running numbered tasks through the orchestrator, the standard command has been:
  `py -m agents.run_task <task-file> --push --keep-runtime-artifacts --provider openai --model gpt-5`
- Prefer narrow fixes. If the runtime or policy surface is the blocker, patch that narrowly.
- If a task output is partial, do not overclaim success.
- Be strict about branch cleanliness and avoid shipping runtime artifacts.
- If `_last_subset_preservation.json` appears in a branch diff, restore it from `origin/main` so it disappears from the branch diff.
- The cadence we’ve been using is:
  zip -> exact apply/validate/merge steps -> run next task -> inspect branch diff -> merge or narrow-fix -> continue

Recent important history:

- Task 172 initially kept regressing shared compatibility surfaces, so we hardened the task definition first and finished it narrowly.
- Task 173 proved too broad, so we split it into 173a and 173b:
  - 173a restored the frozen/shared controller-contract compatibility surface
  - 173b added the bounded supervised dev/test role split additively
- Task 174 added the bounded two-task canary scorecard and benchmark.
- Task 175 recorded the conservative verdict that the bounded supervised two-task pilot is ready, while keeping broader claims blocked.
- We also merged a hygiene PR to clean up `.gitignore`, runtime scratch, and stale local artifacts/branches.

What to do in the new chat:

- Review the uploaded current-main snapshots first.
- Keep numbering aligned from 176 onward.
- Do not drift into broad multi-task autonomy or standalone product claims.
- Keep the next tranche focused on exact two-task pilot operation, curated pair evidence, supervision truth, and conservative widening checkpoints.
- After I merge the new planning/docs patch, I will provide the same files again from updated `main`.
