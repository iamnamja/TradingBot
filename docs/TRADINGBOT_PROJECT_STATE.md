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
