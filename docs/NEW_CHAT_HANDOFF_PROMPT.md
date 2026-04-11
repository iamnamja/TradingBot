We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth.

Current state:

- repo is complete through Task 165,
- the orchestrator has a bounded external-safe one-task lane with multi-agent dev/test/repair/controller artifacts,
- benchmark scorecard integration, empty-bundle retry classification, subset-preservation normalization, completion integrity gating, authority-gate evidence narrowing, deliverable-contract hardening, runtime artifact hygiene cleanup, and a second one-task reliability re-proof are in place,
- the project is still in one-task reliability mode,
- broad multi-task autonomy is still not justified yet.

What matters most now:

- keep the next tranche focused on one-task reliability and promotion truth,
- improve strict no-manual scorecard truth,
- narrow authority ambiguity without weakening conservative claim discipline,
- eliminate the dominant remaining one-task failure family,
- only then decide whether the orchestrator should become the default path for eligible one-task work and whether a bounded two-task pilot is justified.

Planned next tranche:

- 166 orchestrator_strict_no_manual_intervention_scorecard
- 167 orchestrator_authority_corroboration_and_run_truth
- 168 orchestrator_top_failure_family_elimination_tranche
- 169 orchestrator_one_task_promotion_reproof
- 170 orchestrator_default_single_task_path_and_two_task_pilot_gate

Working style:

- review uploaded current main files first,
- keep patches narrow,
- preserve public/runtime surfaces unless there is a compelling measured reason not to,
- use orchestrator-run mode when the runtime is stable enough,
- use small manual engine fixes only when the runtime itself is the blocker,
- after each change provide exact PowerShell apply/validate/merge steps.
