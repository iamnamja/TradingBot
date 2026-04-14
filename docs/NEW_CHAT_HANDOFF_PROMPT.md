We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth. I will upload current `agents.zip`, `src.zip`, `tasks.zip`, `tests.zip`, and sometimes the root `README.md` from merged `main`.

Current state:

- repo is complete through Task 180,
- the one-task lane is conditionally ready under supervision and remains the default proving path,
- the bounded supervised two-task pilot is now explicitly ready on a curated adjacent-pair corpus and has:
  - an exact two-task pilot runner and pair ledger,
  - a curated adjacent-pair corpus and admission manifest,
  - supervised-intervention truth and failure-digest artifacts,
  - a real bounded corpus benchmark,
  - a bounded-corpus promotion/checkpoint artifact,
- broad unattended multi-task autonomy is still not justified,
- standalone orchestrator-as-its-own-app remains blocked.

Honest posture right now:

- one-task work is the default supervised proving path,
- bounded supervised two-task pilot work is ready on the curated adjacent-pair corpus,
- widening beyond that is still blocked until more evidence exists,
- capability widening is paused temporarily because the next tranche is reliability first.

Why the next tranche changed:

- recent work proved the bounded pilot surfaces exist,
- but task runs still show recurring runtime fragility,
- compatibility/import/public-surface drift can still derail otherwise-correct tasks,
- proof-task admission can still block execution when exact deliverable contracts are missing,
- the next bottleneck is now runtime reliability, not the absence of a bounded pilot.

Next planned tranche:

- 181 orchestrator_failure_family_taxonomy_and_repair_target_selection
- 182 orchestrator_import_contract_and_additive_compatibility_guardrails
- 183 orchestrator_resume_checkpoint_and_attempt_state_reentry
- 184 orchestrator_reliability_benchmark_and_regression_matrix
- 185 orchestrator_reliability_checkpoint_and_capability_resume_gate

Strategic direction:

- Phase A: one-task truth established enough to serve as the default supervised path.
- Phase B: bounded supervised two-task pilot established and exercised conservatively on curated adjacent-pair corpus.
- Phase C: reliability-first hardening of runtime classification, compatibility guardrails, and resume/re-entry.
- Phase D: only after the reliability checkpoint can capability widening resume cautiously.
- Phase E: standalone orchestrator-app work remains later and blocked.

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
  7. commit/push/create PR/merge with auto-merge
  8. reset back to clean `main`
- When running numbered tasks through the orchestrator, the standard command has been:
  `py -m agents.run_task <task-file> --push --keep-runtime-artifacts --provider openai --model gpt-5`
- Prefer narrow fixes. If runtime or policy surface is the blocker, patch that narrowly.
- If a task output is partial, do not overclaim success.
- Be strict about branch cleanliness and avoid shipping runtime artifacts.
- If `_last_subset_preservation.json` appears in a branch diff, restore it from `origin/main` so it disappears from the branch diff when the file is tracked. If it is not tracked, do not force anything.
- The cadence has been:
  zip -> exact apply/validate/merge steps -> run next task -> inspect branch diff -> merge or narrow-fix -> continue

Recent important history:

- Task 176 initially failed on a ledger artifact-path convention and then recovered narrowly.
- Task 177 was a narrow additive manifest step and merged cleanly.
- Task 178 added supervised intervention and pilot failure digest truth.
- Task 179 first failed because benchmark compatibility/public-surface expectations were not stable enough; we hardened the task contract and reran it additively as `bounded_corpus_benchmark.py`.
- Task 180 first failed at proof-task admission because the exact deliverable contract was missing; we hardened the task spec and reran it cleanly.
- Through Task 180, the repeated lesson was that reliability and compatibility are now the main bottleneck.

What to do in the new chat:

- Review the uploaded current-main snapshots first.
- Keep numbering aligned from 181 onward.
- Do not drift into broad multi-task autonomy claims.
- Keep the next tranche focused on runtime reliability: failure-family classification, repair-target precision, compatibility guardrails, resume-safe recovery, and measurable reliability evidence.
- After I merge the new planning/docs patch, I will provide the same files again from updated `main`.
