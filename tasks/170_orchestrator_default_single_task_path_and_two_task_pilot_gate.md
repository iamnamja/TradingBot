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

## Operator-facing policy

- Default path (single task):
  - The orchestrator’s bounded one-task lane is the default path for benchmark-eligible tasks under light supervision.
  - Eligibility is the same external-safe profile used in the curated benchmark (strict deliverable contract, protected/meta harness untouched, validation profile available).
  - This default does not change the supervisor’s approval checkpoints or the final-acceptance guardrails.

- Explicit two-task pilot gate:
  - Any future two-task widening must be explicitly gated and strictly bounded to 2 tasks.
  - Preconditions:
    - Promotion verdict is one of: ready_to_be_default, conditionally_ready_under_supervision.
    - An explicit operator flag requests the pilot (operator_pilot_flag=True).
    - All existing guardrails (protected-file policy, exact deliverable contract, validation) remain in force.
  - Out of scope: any general multi-task autonomy. This task does not enable it and does not claim it.

## Machine-readable contract

- New helpers in agents.lib.task_queue (wrapped by agents.run_task for stability):
  - two_task_readiness_gate_snapshot() — returns a structured policy snapshot including:
    - gate_enabled=True
    - default_single_task_path=True
    - pilot_ready_verdicts=("ready_to_be_default","conditionally_ready_under_supervision")
    - explicit_operator_flag_required=True
    - bounded_two_task_limit=2
    - widening_to_general_multi_task_forbidden=True
  - evaluate_two_task_readiness_gate(promotion_verdict, operator_pilot_flag, bounded_limit_requested=None) — returns:
    - allowed: bool
    - bounded: True
    - bounded_limit: int (<=2)
    - preconditions: list[str]
    - reason: str
  - plan_two_task_phase_transition(current_phase, evaluation) — computes the conservative phase transition:
    - single_task_default -> two_task_pilot only when evaluation.allowed is True.

- A light selector for the single-task default path:
  - select_single_admissible_safe_task(manifest, repo_root=".") — recommends one eligible task path without widening.

## Acceptance criteria

- Docs clearly state whether the orchestrator is now the default path for eligible one-task work.
- Docs clearly state the preconditions for any future two-task pilot.
- No claim is made that broad multi-task autonomy is ready unless the preceding promotion task explicitly says so.
