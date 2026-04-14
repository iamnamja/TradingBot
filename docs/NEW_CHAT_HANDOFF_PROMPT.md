We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth. I will upload current `agents.zip`, `docs.zip`, `tasks.zip`, `tests.zip`, and sometimes the root `README.md` from merged `main`.

Current state:

- repo is complete through Task 185,
- the one-task lane is conditionally ready under supervision,
- the bounded supervised two-task pilot is ready in bounded supervised scope,
- the reliability-first tranche 181–185 is complete,
- a post-185 reliability checkpoint exists and the verdict is still conservative: conditionally ready under supervision,
- the project still does **not** claim broad unattended multi-task autonomy,
- standalone orchestrator-as-its-own-app work remains blocked.

Honest posture right now:

- one-task work is still the default proving path under supervision,
- bounded supervised two-task pilot work is valid on the curated corpus,
- any widening remains bounded and cautious,
- broad unattended multi-task autonomy is still not justified,
- standalone productization remains blocked.

Most recent important lessons:

- repeated manual fixes were needed because `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md` can drift on status headlines,
- a `gpt-5-codex` run did not prove generic Codex compatibility; it failed in bundle transport because the harness still assumes a strict GPT-style file bundle,
- the provider/model selection layer may be flexible, but the output-contract layer is not yet sufficiently model-aware.

Next planned tranche:

- 186 orchestrator_docs_status_headline_consistency_guard
- 187 orchestrator_model_profile_registry_and_output_transport_contract
- 188 orchestrator_codex_patch_transport_and_dual_mode_output_parsing
- 189 orchestrator_provider_capability_negotiation_and_safe_model_fallback
- 190 orchestrator_contract_and_model_transport_checkpoint_and_next_slice_gate

Strategic direction:

- Phase A: truthful one-task path
- Phase B: bounded supervised two-task pilot
- Phase C: reliability-first hardening complete through 185
- Phase D: contract and model-compatibility hardening through 190
- Phase E: only after the post-190 checkpoint, consider a cautious bounded next capability slice
- Phase F: standalone orchestrator app remains later and blocked

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

What to do in the new chat:

- Review the uploaded current-main snapshots first.
- Keep numbering aligned from 186 onward.
- Do not drift into broad multi-task autonomy or standalone product claims.
- Keep the next tranche focused on docs/status consistency, explicit model profiles, dual transport support, and a conservative post-transport checkpoint.
- After I merge the new planning/docs patch, I will provide the same files again from updated `main`.
