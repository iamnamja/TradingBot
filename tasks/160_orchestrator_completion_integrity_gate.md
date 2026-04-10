# Task 160 — orchestrator completion integrity gate

## Why

The Task 157 live run showed a failure mode where the orchestrator generated a plausible helper and passing tests but did not integrate the change into the actual benchmark/session surfaces required by the task. We need the system to distinguish partial helper-only success from true task completion.

## Scope

Add a completion-integrity gate for proof-mode tasks.

## Requirements

- Evaluate whether changed files actually cover the task’s required integration surfaces, not just local helper/test additions.
- Allow narrow task-specific deliverable contracts to declare required integration targets.
- Treat helper-only partials as incomplete when the task requires benchmark/session/runtime integration.
- Keep the rule conservative and compatible with the existing proof-task admission model.

## Acceptance criteria

- Tests prove that helper-plus-test-only outputs are rejected for tasks that require integration into live benchmark/session paths.
- Tests prove that true integrated completions still pass the integrity gate.
- Task outputs and docs explain why a run was marked incomplete when coverage is too narrow.
