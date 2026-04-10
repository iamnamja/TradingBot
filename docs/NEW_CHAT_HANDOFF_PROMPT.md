We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth.

Current state:

- repo is complete through Task 155,
- the orchestrator has a bounded external-safe one-task lane with multi-agent dev/test/repair/controller artifacts,
- failure taxonomy, scoreboarding, failure digesting, a truthful two-task readiness gate, and bounded lint-only preflight are in place,
- the two-task gate is still a truthful no-go,
- the next phase is benchmark proof mode, not widening.

What matters most now:

- use the orchestrator itself to run benchmark-eligible one-task work,
- treat any human mid-run intervention as a failed autonomous benchmark run,
- preserve compatibility seams and public surfaces,
- reduce measured real blockers rather than broadening claims.

Planned next tranche:

- 156 orchestrator_one_task_autonomous_benchmark_harness
- 157 orchestrator_strict_no_manual_intervention_scorecard
- 158 orchestrator_authority_corroboration_and_run_truth
- 159 orchestrator_top_failure_family_elimination_tranche
- 160 orchestrator_one_task_promotion_reproof

Working style:

- review uploaded current main files first,
- keep patches narrow,
- prefer targeted repairs over rewrites,
- preserve public/runtime surfaces unless there is a compelling reason not to,
- after each change provide exact PowerShell apply/validate/merge steps.
