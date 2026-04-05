# Task 089 — Orchestrator hardened autonomous short-manifest proof

## Why this task exists

Task 082 established the first ordinary-manifest autonomous proof slice. After the 083–088 hardening work, the project needs an updated proof showing that the controller contract, retry/self-heal channel, merge/resume truth, and strict-mode discipline now work together more reliably.

## Outcome

Produce a hardened autonomous short-manifest proof that consumes the now-canonical controller contract and strict-mode safeguards.

## Create or update these exact files

- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior

The proof must cover a short ordinary manifest where the orchestrator can honestly demonstrate:

1. task execution
2. authoritative validation
3. final acceptance review
4. retryable self-heal without raw re-execution
5. accepted-task PR/check/merge/reset gate
6. truthful stop on merge-posture failure
7. truthful resume-after-merge behavior
8. no premature proof-complete claims before the proof is actually green

## Tests

Add or adjust deterministic local proof tests that demonstrate:

1. acceptance + non-reexecuting self-heal + continue
2. honest stop on failed merge/checks/reset posture
3. resume-after-merge skip semantics based on persisted truth
4. controller strict-mode and claim-deferral behavior for proof-shaping tasks

## Guardrails

- Keep proof scope narrow and honest
- Do not claim arbitrary protected/controller task-list autonomy
- Keep deterministic local proofs as the source of truth for this task
- Treat this as a proof-and-doc synchronization task, not a new controller-core feature tranche

## Acceptance

This task is complete when the repo can honestly claim a hardened short-manifest ordinary-task autonomy proof backed by green deterministic tests and synchronized docs.
