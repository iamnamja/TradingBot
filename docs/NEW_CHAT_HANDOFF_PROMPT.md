We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth.

Current state:

- repo is complete through Task 170,
- the one-task lane is conditionally ready under supervision,
- tasks 157–170 established strict scorecard truth, deliverable-contract and completion-integrity enforcement, authority corroboration, runtime artifact hygiene, a one-task promotion verdict, and an explicit future two-task pilot gate,
- the repo is **not** claiming broad multi-task autonomy yet,
- the standalone orchestrator-as-its-own-app phase is still blocked behind bounded two-task pilot proof.

What matters most now:

- keep one-task truth intact,
- prepare the smallest credible adjacent two-task pilot under supervision,
- do not widen past what benchmark and re-proof artifacts justify,
- use explicit thresholds and durable artifacts rather than prose optimism.

Planned next tranche:

- 171 orchestrator_two_task_pilot_admission_and_eligibility_truth
- 172 orchestrator_dependency_aware_two_task_handoff_contract
- 173 orchestrator_supervised_dev_test_role_split_for_bounded_pilot
- 174 orchestrator_two_task_canary_scorecard_and_benchmark
- 175 orchestrator_bounded_two_task_pilot_reproof_and_product_checkpoint

Working style with the user:

- The user uploads current `agents.zip`, `docs.zip`, `tasks.zip`, `tests.zip`, and sometimes root `README.md` from merged `main`.
- First review those uploaded current-main snapshots before planning the next tranche.
- Then provide a **zip patch** containing the updated docs/tasks (and code files only when explicitly requested for a code patch).
- After providing the zip, give exact PowerShell commands to:
  1. reset to clean `main`,
  2. create a branch,
  3. optionally delete stale duplicate task files before applying the zip,
  4. expand/copy the zip into the repo,
  5. inspect diffs,
  6. run validation,
  7. commit/push/create PR/merge,
  8. reset back to clean `main`.
- When running actual numbered tasks through the orchestrator, the standard command has been:
  `py -m agents.run_task <task-file> --push --keep-runtime-artifacts --provider openai --model gpt-5`
- When a run fails, inspect the console output plus retained artifacts like `_last_agent_model_output.txt`, `_last_agent_file_bundle.txt`, and `_last_subset_preservation.json` if relevant.
- Prefer **narrow fixes**. If the runtime or policy surface is the blocker, patch that narrowly. If the task output is partial, do not overclaim success.
- Be strict about branch cleanliness and avoid letting runtime artifacts ship. If `_last_subset_preservation.json` appears in a branch diff, restore it from `origin/main` and commit the restoration so it disappears from the branch diff.
- The user likes a consistent cadence: zip -> exact apply/validate/merge steps -> next task.

Current strategic direction:

- Phase A: one-task truth is established enough to serve as the default supervised proving path.
- Phase B: bounded supervised two-task pilot preparation is next.
- Phase C: only after a successful two-task pilot re-proof should the project move toward productizing the orchestrator as a separate app that can build other apps.
