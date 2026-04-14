# Task 182 — orchestrator import contract and additive compatibility guardrails

## Why

Recent work showed that benchmark and runner changes can still regress shared import/public surfaces if additive expectations are not explicit enough. The repo needs narrower guardrails here before capability widening resumes.

## Scope

Harden import/public compatibility contracts and additive-surface guarantees for shared orchestrator modules.

## Runtime seams to reuse

- Reuse the existing one-task benchmark compatibility surface.
- Reuse the bounded two-task canary compatibility surface.
- Reuse the bounded corpus benchmark entrypoint added in Task 179.
- Reuse static-contract enforcement and protected-surface checks where available.

## Requirements

- Identify the orchestrator public/import surfaces that recent tasks depended on, including benchmark, runner, and bounded corpus entrypoints.
- Add compatibility guardrails so future additive work is less likely to break those surfaces.
- Preserve the existing one-task and canary benchmark compatibility surfaces exactly unless a compatibility alias is explicitly required.
- Keep bounded corpus work additive rather than replacement-oriented.
- Add tests that would have caught the kind of compatibility/import regression that Task 179 initially hit.

## Create or update these exact files

- `src/builder/orchestrator/benchmark.py`
- `src/builder/orchestrator/bounded_corpus_benchmark.py`
- `tests/test_benchmark_live_scorecard_integration.py`
- `tests/test_benchmark_scorecard_integration.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/182_orchestrator_import_contract_and_additive_compatibility_guardrails.md`

## Non-goals

- Do not redesign benchmark scoring semantics.
- Do not replace the strict one-task benchmark session.
- Do not reopen broader capability widening.

## Acceptance criteria

- Shared benchmark and runner compatibility surfaces are explicitly guarded.
- Tests would fail if additive bounded-corpus work regressed the one-task or canary compatibility surfaces.
- Docs record that this task is reliability hardening, not a capability expansion.

## Implementation notes

- Favor compatibility aliases, explicit exports, and additive wrapper discipline over broad module restructuring.
