# Orchestrator Transport Stability and Observability Guide (191–195)

## Goal of this tranche

The goal is to stop transport failures from being black boxes.

This tranche is not about broadening autonomy. It is about making the runner tell the truth quickly when transport and capture fail.

## Known operational problem

On some tasks, especially transport-sensitive or protected-surface tasks, the run can fail before lint/tests with symptoms like:
- selected provider/model marked compatible,
- required transport marked `file_bundle`,
- raw output length recorded as `0`,
- parsed bundle reduced to `BEGIN_FILE_BUNDLE / END_FILE_BUNDLE` only,
- and no actionable explanation of whether the failure was response capture, parser mismatch, or persistence.

## What this tranche should accomplish

### Capture integrity
- preserve non-empty raw model output whenever it exists
- if output is empty, write an explicit capture-failure reason

### Transport-failure artifacts
- store parser path attempted
- store required and selected transport
- store retry count and artifact lengths
- store whether protected-method mode was selected and why

### Preflight and retry discipline
- protected-method mode should record why it was chosen
- retries should record what changed between attempts
- fallback should be explicit, not implicit

### Benchmarking and checkpointing
- measure transport failure families over real runs
- only reopen cautious next-slice planning if transport stability improves materially

## Operator guidance

- continue using `gpt-5` as the known-good baseline unless a task explicitly proves another path
- prefer narrow runner/instrumentation changes
- treat empty raw output as a first-class failure family, not a generic parse failure
- preserve artifact hygiene and avoid broad doc churn in runtime-focused tasks
