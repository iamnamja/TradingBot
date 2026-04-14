# Task 173 — orchestrator supervised dev-test role split for bounded pilot

## Why

The bounded two-task pilot should not rely on vague “multi-agent” language. The runtime already has an explicit role model — `controller`, `builder`, and `verifier` — and the pilot should reuse that model rather than inventing a second role taxonomy. The smallest credible next step is to make the builder/verifier split explicit for bounded supervised pilot work while preserving controller authority.

Fresh reruns also showed a repeat failure family: the implementation tends to replace or narrow frozen controller-contract and single-task reporting surfaces instead of extending them. This task must therefore be treated as a bounded extension task, not a refactor or simplification task.

## Scope

Introduce an explicit supervised dev/test role split for bounded two-task pilot work by reusing the existing builder/verifier/controller model **without replacing or narrowing existing public/frozen surfaces**.

## Runtime seams to reuse

- Reuse the role taxonomy and handoff surfaces in `agents.lib.multi_agent_contract`.
- Reuse `agents.lib.multi_agent_loop` for role sequencing and controller authority.
- Reuse existing role-trace and artifact capture in `agents.run_single_task`.
- Do not add new autonomous role types for this task.

## Frozen compatibility surfaces that must remain intact

This task is not allowed to replace these with slimmer or alternate contracts. Existing consumers and tests must continue to work.

- `agents/lib/multi_agent_contract.py`: preserve (and only extend) `multi_agent_contract_snapshot`, `allowed_role_handoff`, `controller_decides_next_role`, `canonical_role_handoff_state`, `resume_role_handoff_state`, `canonical_role_artifact_envelope`, `summarize_role_artifact_envelope`, `empty_role_artifact_envelopes`, and `orchestrator_package_boundary_snapshot`.
- Preserve existing snapshot keys and aliases already used by older tests and batch-state code, including role lists, specialist-role lists, handoff/artifact field-name lists, `pending_role`, and permissive envelope normalization for existing callers.
- `agents/lib/multi_agent_loop.py`: extend bounded pilot sequencing additively; do not remove existing compatibility keys expected by older callers such as local-first supervised mode/status surfaces.
- `agents/run_single_task.py`: preserve existing single-task reporting, canary metrics, supervised handoff, operator proof bundle, and artifact-writing helpers; add pilot sequence checkpoint truth on top of those surfaces.

## Requirements

- Treat the pilot’s “dev” role as the existing `builder` role and the “test” role as the existing `verifier` role.
- Keep `controller` as the only role allowed to approve the next role transition.
- Make the pilot role sequence explicit and inspectable in artifacts or checkpoints.
- The runtime must stop conservatively when the requested role sequence is unsupported or when controller authority would be bypassed.
- Keep this split bounded to the supervised pilot lane; do not claim general autonomous multi-agent execution.
- Do not delete snapshot keys, remove aliases, narrow function signatures, or change defaulting behavior that older tests or consumers still rely on.
- Do not rewrite `multi_agent_contract.py` or `run_single_task.py` into minimal alternate contracts.

## Acceptance criteria

- Tests prove the bounded pilot lane distinguishes builder and verifier responsibilities explicitly.
- Tests prove the controller remains the sole authority for next-role decisions.
- Tests prove the runtime stops conservatively when an unsupported role sequence is requested.
- Existing frozen/public surfaces named above still load and behave compatibly after the change.
- Full repo validation is green with:
  - `python -m ruff check .`
  - `python -m pytest -q`
- Docs explain that this is supervised builder/verifier separation for the bounded pilot, not broad autonomous multi-agent execution.

## Notes

This task makes the dev/test split explicit **within** the existing builder/verifier/controller model. It does not introduce a new general multi-agent runtime, does not widen into autonomous role negotiation, and does not justify broad multi-task autonomy.

## Implementation notes

- Pilot aliasing is additive:
  - `dev` => `builder`
  - `test` => `verifier`
- The explicit bounded pilot sequence should remain limited to:
  - `builder -> verifier -> controller`
  - `verifier -> builder -> controller`
- Unsupported sequences must stop conservatively with an inspectable reason.
- Any checkpoint or artifact added for this task should append fields rather than replace existing single-task or controller-contract surfaces.
