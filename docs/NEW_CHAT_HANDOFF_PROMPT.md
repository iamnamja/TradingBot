We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth. I will upload current `agents.zip`, `docs.zip`, `tasks.zip`, `tests.zip`, and sometimes the root `README.md` from merged `main`.

Current state:

- repo is complete through Task 190,
- the one-task lane is conditionally ready under supervision,
- the bounded supervised two-task pilot remains valid in bounded supervised scope,
- the reliability-first tranche 181–185 is complete,
- the contract/model compatibility tranche 186–190 is complete,
- the project still does **not** claim broad unattended multi-task autonomy,
- standalone orchestrator-as-its-own-app work remains blocked.

Honest posture right now:

- one-task work is still the default proving path under supervision,
- bounded supervised two-task pilot work is valid on the curated corpus,
- any widening remains bounded and cautious,
- broad unattended multi-task autonomy is still not justified,
- standalone productization remains blocked.

Most recent important lessons:

- repeated docs/status drift required a guard,
- model profiles and transport contracts needed to become explicit,
- capability negotiation and fallback now exist,
- but transport failures can still occur before lint/tests with effectively empty raw output and empty parsed bundles,
- so the next bottleneck is observability and capture integrity, not autonomy widening.

Next planned tranche:

- 191 orchestrator_raw_model_output_capture_integrity_and_nonempty_artifact_guarantee
- 192 orchestrator_transport_failure_artifact_expansion_and_parser_path_observability
- 193 orchestrator_protected_method_preflight_fallback_tracing_and_retry_discipline
- 194 orchestrator_transport_health_benchmark_and_failure_family_corpus
- 195 orchestrator_transport_stability_checkpoint_and_cautious_autonomy_resume_gate

Strategic direction:

- Phase A: truthful one-task path
- Phase B: bounded supervised two-task pilot
- Phase C: reliability-first hardening complete through 185
- Phase D: contract/model compatibility hardening complete through 190
- Phase E: transport stability and observability hardening through 195
- Phase F: only after the post-195 checkpoint, consider a cautious bounded next capability slice
- Phase G: standalone orchestrator app remains later and blocked

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
