We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth.

Current state:

- repo is complete through Task 156,
- the orchestrator has a bounded external-safe one-task lane with multi-agent dev/test/repair/controller artifacts,
- failure taxonomy, scoreboarding, failure digesting, a truthful two-task readiness gate, bounded lint-only preflight, and an initial benchmark harness are in place,
- the two-task gate is still a truthful no-go,
- the current bottleneck is one-task reliability in live proof-mode runs.

What matters most now:

- use the orchestrator itself to run benchmark-eligible one-task work,
- treat any human mid-run intervention as a failed autonomous benchmark run,
- preserve compatibility seams and public surfaces,
- reduce measured real blockers rather than broadening claims,
- prefer runtime and integration hardening over adding new generic autonomy features.

Planned next tranche:

- 157 orchestrator_benchmark_scorecard_integration
- 158 orchestrator_empty_bundle_transport_retry_and_classifier
- 159 orchestrator_runtime_artifact_quarantine_and_subset_preservation_normalization
- 160 orchestrator_completion_integrity_gate
- 161 orchestrator_one_task_reliability_minipack_reproof

Working style:

- review uploaded current main files first,
- keep patches narrow,
- prefer targeted repairs over rewrites,
- preserve public/runtime surfaces unless there is a compelling reason not to,
- after each change provide exact PowerShell apply/validate/merge steps.
