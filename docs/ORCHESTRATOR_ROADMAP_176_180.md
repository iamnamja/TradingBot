# Orchestrator Roadmap — Tasks 176–180

## Current tranche posture

The repo is now past bounded two-task pilot preparation and re-proof.

The next tranche should not jump to broad multi-task autonomy. It should operationalize the bounded supervised two-task pilot and gather real pair-level evidence.

The order for this tranche is:

- 176 — bounded two-task pilot runner and pair ledger
- 177 — curated adjacent-pair corpus and admission manifest
- 178 — supervised intervention artifact and pilot failure digest
- 179 — real bounded two-task corpus benchmark
- 180 — bounded two-task corpus re-proof and widening checkpoint

## What changed at Task 175

Tasks 171–175 established:

- explicit two-task pilot admission truth
- explicit adjacent A->B handoff truth
- bounded supervised builder/verifier role split
- durable two-task canary scorecard and promotion artifacts
- a conservative verdict that the bounded supervised two-task pilot is ready

That means the repo now has permission to exercise a bounded supervised two-task pilot — but not to widen past it yet.

## Guardrails for Tasks 176–180

- Keep scope at exactly two tasks per bounded pilot run.
- Reuse the existing admission, handoff, role-split, benchmark, and promotion surfaces.
- Keep one-task truth intact and unchanged.
- Persist operator/supervised intervention truth explicitly so human help never gets counted as autonomous success.
- Prefer curated adjacent-task pairs over broad backlog selection.
- Do not claim broad multi-task autonomy or standalone product readiness in this tranche.

## Desired outcome of the tranche

By the end of this slice, the repo should have:

- a real bounded two-task pilot runner,
- a curated pilot pair corpus and manifest,
- durable pair-level ledgers and supervision/intervention artifacts,
- a real corpus benchmark over those bounded pilot pairs,
- and an honest checkpoint about whether the bounded supervised two-task pilot should continue as-is, expand cautiously, or remain blocked.

## What is still explicitly out of scope

- three-task or arbitrary-length manifest autonomy
- unattended multi-task scheduling
- general multi-agent role orchestration across arbitrary work
- standalone orchestrator product extraction
