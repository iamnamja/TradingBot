We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth. I will upload current `agents.zip`, `docs.zip`, `tasks.zip`, `tests.zip`, `src.zip`, and sometimes the root `README.md` from merged `main`.

Current state:

- repo is complete through Task 195,
- the one-task lane is conditionally ready under supervision,
- the bounded supervised two-task pilot remains the only justified multi-task form,
- the reliability-first tranche 181-185 is complete,
- the contract/model compatibility tranche 186-190 is complete,
- the transport stability and observability tranche 191-195 is complete,
- the project still does **not** claim broad unattended multi-task autonomy,
- standalone orchestrator-as-its-own-app work remains blocked.

Most important recent lesson:

- the orchestrator was repeatedly failing before lint/tests because provider chat could still collapse through runtime-foundations compatibility shims into provider-client placeholder stubs that returned empty text.
- after a long debugging cycle, we fixed the known-provider chat path so runtime execution now stays on local provider implementations for real providers.
- after that fix, Tasks 191-195 ran successfully and the transport-stability tranche completed.

Honest posture right now:

- one-task work is still the default proving path under supervision,
- bounded supervised two-task pilot work is still the only justified multi-task lane,
- transport behavior is much more observable and stable than before,
- broad unattended multi-task autonomy is still not justified,
- standalone productization remains blocked.

Current phase order:

1. truthful one-task path
2. bounded supervised two-task pilot
3. reliability-first hardening
4. contract and model compatibility hardening
5. transport stability and observability hardening
6. post-transport execution reproof
7. cautious bounded capability widening
8. standalone orchestrator app extraction

Next planned tranche:

- 196 orchestrator_post_transport_one_task_rebenchmark_and_empty_output_regression_guard
- 197 orchestrator_transport_stable_bounded_two_task_pilot_rerun_and_scorecard_refresh
- 198 orchestrator_adjacent_pair_resume_precision_and_checkpointed_reentry_truth
- 199 orchestrator_supervised_three_step_canary_admission_and_chain_contract
- 200 orchestrator_post_transport_execution_checkpoint_and_bounded_next_slice_gate

Strategic direction:

- The transport-stability tranche is complete, but that does not authorize broader autonomy claims.
- The next tranche must reprove one-task and bounded two-task execution on the recovered runtime path.
- Only after those proofs hold should the project define a very small supervised widening step.
- Any post-200 verdict must stay conservative and supervision-aware.

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
- Prefer narrow fixes. If runtime or policy surface is the blocker, patch that narrowly.
- If a task output is partial, do not overclaim success.
- Be strict about branch cleanliness and avoid shipping runtime artifacts.
- If `_last_subset_preservation.json` appears in a branch diff, restore it from `origin/main` so it disappears from the branch diff.
- Runtime/debug artifacts like `_last_model_capability.txt`, `_last_provider_call_path.txt`, `_last_raw_output_meta.txt`, and `_last_protected_method_preflight.json` should stay ignored and never merge.
- The cadence we’ve been using is:
  zip -> exact apply/validate/merge steps -> run next task -> inspect branch diff -> merge or narrow-fix -> continue

What to do in the new chat:

- Review the uploaded current-main snapshots first.
- Keep numbering aligned from 196 onward.
- Do not drift into broad unattended multi-task autonomy or standalone product claims.
- Keep the next tranche focused on post-transport execution reproof, bounded two-task refresh, resume precision, and only the smallest supervised widening step.
- After I merge the new planning/docs patch, I will provide the same files again from updated `main`.
- Include precise PowerShell apply/validate/merge steps the same way we have been doing.

Important note:

- On the next handoff, include the root `README.md` alongside the zip snapshots so repo-top status text stays synchronized with `docs/TRADINGBOT_PROJECT_STATE.md` and `docs/README.md`.
