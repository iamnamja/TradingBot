# Task 091 — Orchestrator builder/verifier/controller loop

## Why this task exists

Task 090 creates a canonical multi-agent role contract, but the orchestrator still needs an actual role-separated loop.

The desired posture is:

- builder/coder role proposes the implementation patch
- verifier/tester role runs focused and full validation and summarizes evidence
- controller/orchestrator role decides whether to accept, repair, retry, stop, or advance

## Outcome

Implement a canonical sequential builder/verifier/controller loop on top of the existing batch executor and final-acceptance surfaces.

## Create or update these exact files

- `agents/lib/multi_agent_loop.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Canonical loop order

For eligible task families, the orchestrator should execute this explicit role order:

1. controller chooses builder role
2. builder produces patch/result bundle
3. controller chooses verifier role
4. verifier runs focused/full validation and produces verdict/evidence bundle
5. controller decides whether to accept, repair, stop, or advance

### 2) Role-specific artifacts

The loop must produce machine-readable summaries for:

- builder patch attempt
- verifier command/test results
- controller decision

### 3) Verifier as distinct authority

The verifier role must not silently collapse back into builder behavior.

### 4) Conservative control

Controller remains final authority. A passing verifier result does not auto-merge or auto-advance by itself.

## Tests

Add or adjust deterministic tests that prove:

1. the three-role loop runs in canonical order
2. verifier evidence is distinct from builder output
3. controller remains the only authority that advances the task
4. failed verifier results stop or repair according to current policy

## Guardrails

- Keep role execution sequential
- Preserve current acceptance and merge/reset truth rules
- Do not let builder and verifier roles blur into one undifferentiated result shape
- Prefer explicit evidence bundles over inferred behavior

## Acceptance

This task is complete when the orchestrator has a canonical three-role sequential execution loop with distinct builder, verifier, and controller responsibilities.
