# Task 173b — orchestrator supervised dev-test role split for bounded pilot

## Why

Once the shared controller-contract surface is re-proved and stable, the bounded two-task pilot can safely add its explicit supervised dev/test role split.

The pilot should not invent new autonomous role types. It should reuse the repo's existing `builder` / `verifier` / `controller` model, while making the bounded pilot sequence explicit, inspectable, and controller-gated.

## Scope

Add an explicit supervised bounded-pilot role split by mapping pilot `dev` to `builder` and pilot `test` to `verifier`, while keeping `controller` as the sole authority for final next-role approval.

## Runtime seams to reuse

- Reuse the preserved role taxonomy and handoff surfaces in `agents.lib.multi_agent_contract`
- Reuse `agents.lib.multi_agent_loop` for bounded role sequencing and controller gating
- Reuse existing artifact/checkpoint surfaces in `agents.run_single_task`
- Reuse existing single-task durability/reporting helpers; extend them additively

## Requirements

- Treat pilot `dev` as the existing `builder` role.
- Treat pilot `test` as the existing `verifier` role.
- Keep `controller` as the only role allowed to finalize or approve the next transition.
- Make the bounded pilot sequence explicit and inspectable in artifacts or checkpoints.
- Supported bounded sequences must remain conservative:
  - `builder -> verifier -> controller`
  - `verifier -> builder -> controller`
- Unsupported sequences must stop conservatively and explicitly.
- Additive pilot reporting/checkpoint surfaces may include:
  - normalized sequence
  - whether controller gate was required
  - whether the sequence was stopped
  - a bounded-pilot mode indicator where existing tests expect it
- Keep this split bounded to the supervised pilot lane.
- Do **not** claim general autonomous multi-agent execution.

## Non-goals

- Do not widen into arbitrary multi-agent role orchestration.
- Do not add new autonomous role families.
- Do not change preserved controller-contract semantics from `173a`.

## Acceptance criteria

- Tests prove alias mapping:
  - `dev -> builder`
  - `test -> verifier`
- Tests prove the controller remains the sole authority for next-role approval.
- Tests prove unsupported sequences stop conservatively.
- Tests prove the pilot checkpoint/reporting artifact records the explicit bounded sequence and stop state where expected.
- Full repo validation is green:
  - `python -m ruff check .`
  - `python -m pytest -q`
