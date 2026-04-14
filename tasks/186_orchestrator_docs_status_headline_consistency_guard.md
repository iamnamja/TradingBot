# Task 186 — orchestrator docs status headline consistency guard

## Why

Recent successful tasks still required manual cleanup because the repo’s high-level status headlines drifted across `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md`.

The repo needs an explicit guard so narrative state stops lagging behind code and task progress.

## Scope

Add a durable docs-status consistency guard for the repo’s current-state headlines and tranche references.

## Runtime seams to reuse

- Reuse the existing status narrative in `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md`.
- Reuse current task-order and tranche docs under `tasks/` and `docs/`.
- Reuse the reliability-first discipline of small, additive validation helpers.

## Requirements

- Introduce an explicit check for the current status headline and tranche consistency across the repo’s top-level status docs.
- At minimum, guard:
  - `README.md`
  - `docs/TRADINGBOT_PROJECT_STATE.md`
  - any current tranche/index doc that also carries the active task range or status headline
- Keep the guard deterministic and conservative.
- The guard should fail on drift rather than silently rewriting all docs.
- Add tests that would have caught the manual Task 183 and Task 184 headline mismatches.

## Create or update these exact files

- `agents/lib/docs_status_guard.py`
- `tests/test_docs_status_guard.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/186_orchestrator_docs_status_headline_consistency_guard.md`

## Non-goals

- Do not redesign all project docs.
- Do not auto-edit unrelated narrative sections.
- Do not widen capability claims.

## Acceptance criteria

- A deterministic guard exists for the repo status headlines.
- Tests fail when headline task numbers drift across guarded docs.
- Docs explain that this is a contract-hardening step, not a capability step.

## Implementation notes

- Prefer one narrow parser/validator over broad text rewriting.
- It is acceptable to define a small “current status” source-of-truth shape if that keeps the guard stable.
