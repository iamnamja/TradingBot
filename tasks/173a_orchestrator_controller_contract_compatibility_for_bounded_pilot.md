# Task 173a — orchestrator controller-contract compatibility for bounded pilot

## Why

Fresh Task 173 reruns showed that the main failure hotspot is not the new pilot sequencing itself. The real hotspot is the shared controller-contract compatibility surface in `agents.lib.multi_agent_contract.py`, plus a few long-lived consumers that depend on it indirectly through batch state, failure-journal summarization, package-boundary reporting, and single-task proof-bundle helpers.

Before the bounded pilot's dev/test split can be added safely, the repo needs a compatibility-first pass that preserves and re-proves the frozen/shared controller-contract surface.

## Scope

Preserve and restore the shared controller-contract compatibility surface needed by existing repo consumers before adding any new bounded pilot role-sequence behavior.

This is a **compatibility-first** task. It is not the task that introduces the pilot's explicit dev/test role sequence.

## Runtime seams to preserve

Preserve and only extend the following shared surfaces:

- `agents.lib.multi_agent_contract.multi_agent_contract_snapshot`
- `agents.lib.multi_agent_contract.allowed_role_handoff`
- `agents.lib.multi_agent_contract.controller_decides_next_role`
- `agents.lib.multi_agent_contract.canonical_role_handoff_state`
- `agents.lib.multi_agent_contract.resume_role_handoff_state`
- `agents.lib.multi_agent_contract.canonical_role_artifact_envelope`
- `agents.lib.multi_agent_contract.summarize_role_artifact_envelope`
- `agents.lib.multi_agent_contract.empty_role_artifact_envelopes`
- `agents.lib.multi_agent_contract.orchestrator_package_boundary_snapshot`
- any stable single-task proof-bundle/reporting helpers in `agents.run_single_task` that older tests still read
- any stable consumer-bridge / package-boundary wrappers surfaced through `agents.run_task`

## Requirements

- Restore and preserve snapshot keys and aliases that older tests still expect, including at minimum:
  - `roles`
  - `specialist_roles`
  - `controller_next_role_decisions`
  - `artifact_envelope_types`
  - `role_artifact_envelope_field_names`
  - any existing handoff/envelope field inventories that callers still inspect
- Preserve the current `controller_decides_next_role` call shape used by older tests and wrappers, including `proposed_by_role`.
- Preserve `allowed_role_handoff("verifier", "verifier") is False`.
- Preserve `pending_role` reconstruction in resumed handoff state.
- Preserve envelope compatibility for existing callers:
  - task path may be absent/empty in default envelopes
  - `schema_version` must be present
  - verifier verdict information must round-trip correctly
  - existing batch-state and failure-journal callers must remain compatible
- Preserve package-boundary and consumer-bridge compatibility keys, including the nested `consumer_bridge` surface.
- Preserve stable proof-bundle keys that older tests still expect:
  - `bounded_claim_ready`
  - `claim_blockers`
  - `refused_claims`
  - `operator_next_action`
- Keep this task additive and compatibility-preserving.
- Do **not** introduce the new pilot role-sequence behavior here beyond the minimum alias scaffolding needed for compatibility.

## Non-goals

- Do not invent a new alternate contract module.
- Do not simplify or rename public/frozen keys because they look redundant.
- Do not add broad multi-agent autonomy claims.
- Do not add general scheduler behavior.

## Acceptance criteria

- Full repo validation is green:
  - `python -m ruff check .`
  - `python -m pytest -q`
- Existing controller-contract, batch-state, batch-executor, package-boundary, failure-journal, and single-task runner tests remain green.
- The repo exits this task with a controller-contract surface that is stable enough for `173b` to add the bounded pilot role split additively rather than reparatively.
