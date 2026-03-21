# Task 042 — Harness Modularization (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

This tranche exists to modularize `agents/run_task.py` without changing behavior.

## Why this tranche exists

`run_task.py` is now functionally strong but structurally too monolithic. It currently owns:

- parsing the task
- parsing the bundle
- protected-file modes
- semantic preflight
- directive enforcement
- provider/model execution
- retry logic
- git flow
- local check execution

That coupling makes every future change riskier than it needs to be.

## Run order

Run these subtasks in order from clean `main`:

1. `tasks/042a_orchestrator_extract_runtime_foundations.md`
2. `tasks/042b_orchestrator_extract_parsers_and_policies.md`
3. `tasks/042c_orchestrator_extract_semantic_preflight.md`
4. `tasks/042d_orchestrator_thin_run_task_shell_and_parity.md`

## Tranche rule

This is a **no-behavior-change refactor tranche**.

Changes are allowed only when required to preserve compatibility during extraction.

No new orchestrator product behavior should be introduced in 042 beyond what is strictly necessary for modularization and parity validation.

## Acceptance gate

Do not mark Task 042 complete until all four subtasks are green and merged.
