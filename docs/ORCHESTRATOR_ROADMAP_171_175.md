# Orchestrator Roadmap — Tasks 171–175

## Current tranche posture

The repo is past the one-task promotion checkpoint and is now in bounded two-task pilot preparation under supervision.

The order for this tranche is now:

- 171 — two-task pilot admission and eligibility truth
- 172 — dependency-aware adjacent-task handoff contract
- 173a — controller-contract compatibility for bounded pilot
- 173b — supervised dev/test role split for bounded pilot
- 174 — two-task canary scorecard and benchmark
- 175 — bounded two-task pilot re-proof and product checkpoint

## Why 173 was split

Fresh Task 173 reruns showed the main risk was not the pilot role split itself, but the shared controller-contract compatibility surface in `agents.lib.multi_agent_contract.py`.

So 173 is now sequenced in two passes:

- first re-prove and preserve compatibility,
- then add the bounded pilot role split additively.

## Guardrails for the remaining tranche

- Do not weaken or replace frozen/public controller-contract surfaces while adding bounded pilot behavior.
- Reuse existing `builder` / `verifier` / `controller` semantics rather than inventing new autonomous role types.
- Keep all bounded-pilot work supervised and conservative.
- Do not widen into general multi-task or general multi-agent autonomy before 175.
