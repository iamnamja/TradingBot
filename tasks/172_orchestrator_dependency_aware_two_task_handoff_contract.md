# Task 172 — orchestrator dependency-aware two-task handoff contract

## Why

A bounded two-task pilot is only credible if task B receives a deterministic and inspectable handoff from task A. The runtime already has the right seams — `depends_on`, `next_task_may_proceed`, role/artifact envelopes, and the single-task supervised handoff artifact — but fresh reruns showed a repeat failure family: the implementation kept **replacing** frozen public-contract surfaces instead of **extending** them.

This task must therefore be treated as a **bounded extension task**, not a refactor or simplification task.

## Scope

Define and validate a dependency-aware, adjacent-task handoff contract for bounded supervised two-task pilot runs **without replacing or narrowing existing public/frozen surfaces**.

## Runtime seams to reuse

- Reuse `TaskQueueItem.depends_on` and existing queue normalization in `agents.lib.task_queue`.
- Reuse the existing `next_task_may_proceed` truth already surfaced by verifier/controller/final-acceptance flows.
- Reuse the single-task supervised handoff artifact surface in `agents.run_single_task` instead of inventing an unrelated handoff file format.
- Reuse role/artifact envelope concepts in `agents.lib.multi_agent_contract` where they help describe the handoff payload.

## Frozen compatibility surfaces that must remain intact

This task is **not allowed** to replace these with slimmer or alternate contracts. Existing consumers and tests must continue to work.

### `agents/lib/multi_agent_contract.py`
Preserve the existing surface and behavior shape for:
- `multi_agent_contract_snapshot`
- `allowed_role_handoff`
- `controller_decides_next_role`
- `canonical_role_handoff_state`
- `resume_role_handoff_state`
- `canonical_role_artifact_envelope`
- `summarize_role_artifact_envelope`
- `empty_role_artifact_envelopes`
- `orchestrator_package_boundary_snapshot`

Extension is allowed. Replacement or signature narrowing is not.

### `agents/run_single_task.py`
Preserve the existing single-task and proof/reporting helpers, including:
- `build_single_task_canary_metrics`
- `build_single_task_supervised_handoff_artifact`
- `build_live_canary_operator_proof_bundle`

Add adjacent-handoff behavior on top of these helpers instead of replacing them with a smaller alternate surface.

### `agents/lib/task_queue.py`
Preserve existing queue/build/post-task behavior for one-task and controller/batch flows. Add adjacent-handoff classification as an additive helper only.

## Requirements

- Model the minimum durable handoff between adjacent tasks A and B only.
- Distinguish at least:
  - `handoff_ready`
  - `handoff_incomplete`
  - `handoff_incompatible`
- Make explicit whether task B may proceed.
- Record enough context to audit why task B was blocked, including dependency truth and any implicated paths or verification profile relevant to the handoff.
- Persist the handoff artifact on an existing durable single-task supervised-handoff surface.
- Task B must not start when the required handoff truth is incomplete or incompatible.
- **Do not** widen to arbitrary multi-task chains or a general scheduler.
- **Do not** delete snapshot keys, remove aliases, or narrow function signatures that older tests or consumers still rely on.
- **Do not** rewrite `multi_agent_contract.py` into a minimal alternate contract.

## Create or update these exact files

- `agents/lib/task_queue.py`
- `agents/lib/multi_agent_contract.py`
- `agents/run_single_task.py`
- `tests/test_task_queue.py`
- `tests/test_single_task_runner.py`
- `tasks/172_orchestrator_dependency_aware_two_task_handoff_contract.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Acceptance criteria

- Tests prove task B cannot start when task A does not produce a handoff-ready result.
- Tests prove the handoff state is persisted and inspectable.
- Tests prove incompatible dependency or proceed-state truth is reported explicitly rather than collapsing into a generic stop.
- Existing frozen/public surfaces named above still load and behave compatibly after the change.
- Full repo validation is green with:
  - `python -m ruff check .`
  - `python -m pytest -q`
- Docs explain that this is an adjacent bounded-pilot handoff contract added by bounded extension, not broad multi-task chaining.

## Notes

This task explicitly models the A->B interface only. It does not introduce a general scheduler, queue rewriter, or arbitrary DAG traversal policy. Any future widening beyond adjacent handoffs requires a separate proof and admission gate.
