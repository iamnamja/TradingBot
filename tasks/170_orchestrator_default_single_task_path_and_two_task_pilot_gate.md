# Task 170 — orchestrator default single-task path and two-task pilot gate

## Why

If the promotion re-proof says the one-task lane is conditionally ready or ready, we need a disciplined way to make that lane the default for eligible tasks without accidentally widening into uncontrolled multi-task autonomy.

## Scope

Add the policy and documentation needed to make the one-task lane the default path for eligible work, while introducing an explicit gate for any future bounded two-task pilot.

## Requirements

- Do not widen directly to general multi-task execution.
- Define the conditions under which benchmark-eligible one-task work should now default to the orchestrator.
- Define a separate explicit gate for any future bounded two-task pilot.
- Keep the operator-facing truth clear about what is now default, what is still supervised-only, and what remains out of scope.

## Acceptance criteria

- Docs clearly state whether the orchestrator is now the default path for eligible one-task work.
- Docs clearly state the preconditions for any future two-task pilot.
- No claim is made that broad multi-task autonomy is ready unless the preceding promotion task explicitly says so.
