# Task 090 — Orchestrator multi-agent role contract and handoff state

## Why this task exists

Through Task 089, the orchestrator proved a hardened short-manifest autonomous slice, but the execution shell still mostly behaves like one controller directing one generalized coding surface.

The next product goal is broader: a controller that can decide which specialized agent should act next, with separate builder/coder and verifier/test roles rather than one undifferentiated execution lane.

That requires one canonical role contract and persisted handoff state before any stronger multi-agent claim would be honest.

## Outcome

Create a canonical multi-agent role contract and persisted handoff state for a three-role controller model:

- controller/orchestrator
- builder/coder
- verifier/tester

## Create or update these exact files

- `agents/lib/multi_agent_contract.py`
- `agents/lib/controller_contract.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_contracts.py`
- `agents/run_task.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Canonical role vocabulary

Introduce one importable multi-agent contract surface that defines at least:

- canonical role names
- allowed role transitions / handoffs
- handoff metadata fields
- per-role outcome vocabulary
- controller authority over which role runs next

### 2) Persisted handoff truth

Persist enough state for deterministic resume and audit across role handoffs.

At minimum the persisted surface must support:

- active role
- prior role
- role attempt count
- handoff reason
- handoff summary / instructions
- role output summary
- verifier verdict
- controller next-role decision

### 3) Compatibility with current controller contract

The new role contract must compose with, not replace, the canonical controller contract from 083–089.

### 4) Narrow role model

Keep the model intentionally narrow and sequential for the first implementation:

- controller chooses
- exactly one specialized role acts at a time
- no speculative parallel role execution yet

## Tests

Add or adjust deterministic tests that prove:

1. one canonical role vocabulary exists
2. handoff truth is persisted consistently
3. controller remains the only authority that chooses the next role
4. resume logic can reconstruct the active/pending role from persisted truth

## Guardrails

- Do not introduce concurrent free-for-all agent execution
- Do not weaken current controller strict-mode behavior
- Keep role separation explicit and auditable
- Treat this as the foundational multi-agent contract task, not a broad autonomy proof

## Acceptance

This task is complete when the repo has one canonical three-role contract with persisted handoff truth that can support a builder/verifier/controller loop without ambiguity.
