We are continuing the TradingBot / Orchestrator project inside the same ChatGPT project.

Use the latest merged main snapshots as source of truth.

Current state:

- the project now has a bounded external-safe one-task lane plus a merged one-task benchmark harness,
- live proof-mode attempts have exposed the main current weaknesses: empty bundle transport failures, runtime artifact ambiguity, and green-but-partial task completions,
- the truthful two-task gate is still no-go,
- the immediate focus is single-task reliability, not wider autonomy.

What matters most now:

- use the orchestrator itself to run benchmark-eligible one-task work,
- treat any human mid-run intervention as failed autonomous work,
- preserve compatibility seams and public surfaces,
- fix runtime/transport/integration blockers before broadening claims,
- prefer the stable run command and runtime artifacts:
  `py -m agents.run_task <task> --push --keep-runtime-artifacts --provider openai --model gpt-5`

Planned next reliability sprint:

- 161 orchestrator_benchmark_scorecard_integration
- 162 orchestrator_empty_bundle_transport_retry_and_classifier
- 163 orchestrator_runtime_artifact_quarantine_and_subset_preservation_normalization
- 164 orchestrator_completion_integrity_gate
- 165 orchestrator_one_task_reliability_minipack_reproof

Working style:

- review uploaded current main files first,
- keep patches narrow,
- prefer targeted repairs over rewrites,
- preserve public/runtime surfaces unless there is a compelling reason not to,
- after each change provide exact PowerShell apply/validate/merge steps,
- optimize for making one benchmark-eligible task complete really well before widening scope.
