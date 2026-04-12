# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (src/tradingbot)
- Orchestrator engine and control plane (src/builder/orchestrator)
- Agent execution harness (agents)
- Numbered implementation tasks (tasks)
- Documentation and project-state tracking (docs)

## Current state (post-Task 169)

- Tasks 124–168 are complete in bounded supervised scope and have established a strict, no‑manual‑intervention scorecard with hosted‑authority corroboration, durable artifact hygiene, and improved deliverable contracts.
- Task 169 adds an explicit promotion decision point for the bounded one‑task lane:
  - The benchmark scorecard now computes a promotion verdict with explicit thresholds and persists a durable promotion.json alongside scorecard.json.
  - The verdict is one of: not_ready, conditionally_ready_under_supervision, ready_to_be_default.
  - Thresholds are embedded in the artifact to prevent subjective interpretation.

### Promotion thresholds (frozen in code)

- min_pass_rate: 0.60
- min_direct_minus_self_healed_margin: 0.20 (direct completion must be materially better than self‑healed alone)
- max_supervised_rate: 0.10
- max_authority_ambiguity_rate: 0.05
- require_no_compat_regressions: True

### Promotion outcome (current re‑proof)

- Verdict: conditionally_ready_under_supervision
- Rationale (mechanical, threshold‑based):
  - Recent sessions meet or exceed the minimum pass‑rate threshold.
  - Direct completions are consistently at least as frequent as self‑healed completions, but not yet materially higher by the 0.20 margin across the curated set.
  - Supervised/escalation and authority‑ambiguity rates remain low and within conservative bounds.
  - No recurring compatibility seam regressions were observed in the curated benchmark.

This means the one‑task lane remains the recommended default under light supervision for benchmark‑eligible work. The durable promotion.json artifact records a session‑local verdict and metrics used to reach it.

### What still blocks full “default without supervision”

- Increase the direct‑over‑self‑healed margin across the curated set to meet or exceed 0.20.
- Maintain low supervised and authority‑ambiguity rates while improving direct completions.
- Continue monitoring for compatibility seam regressions; any recurrence resets the “ready_to_be_default” decision until eliminated across the benchmark set.

## Evidence and tests

- New tests proving the promotion artifact and thresholds:
  - tests/test_benchmark_scorecard_integration.py exercises artifact persistence and verdict outcomes across:
    - invalidated manual edit vs direct success,
    - equal split of direct and self‑healed (conditional),
    - purely direct success (ready).

## Scope honesty

- No widening to two‑task execution; this task only adds a formal, explicit promotion decision artifact.
- All changes are additive and backward‑compatible with existing benchmark artifacts and scoreboards.

## Post‑Task 170 — orchestrator default single‑task path and two‑task pilot gate

- Default path for eligible one‑task work:
  - The orchestrator’s bounded one‑task lane is now the default path for benchmark‑eligible tasks under light supervision.
  - “Eligible” means the task meets the same external‑safe constraints used by the curated benchmark (deliverable contract intact, protected/meta harness untouched, and validation profile available).
  - Operator supervision remains in place; default does not imply unattended widening.
  - Machine‑readable helpers are available: select_single_admissible_safe_task(...) recommends one eligible task without widening.

- Explicit two‑task pilot gate (not a general widening):
  - Any future two‑task execution must pass an explicit gate. The code exposes a machine‑readable snapshot and evaluation helper:
    - two_task_readiness_gate_snapshot() — documents the policy, allowed promotion verdicts, and the strict bounded limit (2).
    - evaluate_two_task_readiness_gate(...) — requires both:
      - a qualifying promotion verdict in {ready_to_be_default, conditionally_ready_under_supervision}, and
      - an explicit operator pilot flag.
    - plan_two_task_phase_transition(...) — computes a conservative phase transition only when the gate is satisfied.
  - The pilot is strictly bounded to two tasks and remains opt‑in. Widening to general multi‑task autonomy is explicitly out of scope.

- Operator‑facing truth:
  - Default: orchestrator one‑task lane for eligible work, with light supervision.
  - Still supervised‑only: any work that touches protected/meta harness or violates the exact deliverable contract.
  - Out of scope: broad multi‑task autonomy; not claimed or enabled by this task.

These policies are encoded in agents.lib.task_queue and surfaced through thin public wrappers in agents.run_task for compatibility with tests and automation.

### Additional implementation notes

- A light selector is provided to choose a single admissible safe task without widening:
  - select_single_admissible_safe_task(manifest, repo_root=".") picks the first existing manifest task path and reports blocked/non‑existent entries.
- Controller‑contract symbol parity is preserved; task_queue now explicitly re‑exports BatchPostTaskDecision for test and API compatibility.
- Snapshot helpers are deterministic and return primitive values, keeping pytest and ruff checks green.
