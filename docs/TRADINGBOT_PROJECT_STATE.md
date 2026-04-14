# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 185)

- Tasks 157–185 are complete in bounded supervised scope.
- The repo now has:
  - a strict no-manual-intervention one-task scorecard,
  - deliverable-contract and completion-integrity enforcement,
  - authority corroboration and conservative run truth,
  - narrowed top one-task failure-family handling,
  - a durable one-task promotion verdict,
  - an explicit default one-task path,
  - a conservative two-task pilot admission gate,
  - a bounded adjacent-task A->B handoff contract,
  - a supervised builder/verifier role split scoped for the pilot,
  - a durable two-task canary scorecard and benchmark artifacts integrated into the existing benchmark session directory,
  - a real bounded two-task pilot runner exercised over a curated adjacent-pair corpus,
  - a bounded two-task pilot re-proof with explicit canary and corpus-backed promotion payloads,
  - import/public compatibility guardrails for orchestrator benchmark surfaces to prevent additive regressions (Task 182),
  - reliability benchmark artifacts and a regression matrix (Task 184),
  - a durable post-185 reliability checkpoint and explicit capability-resume gate (Task 185).

## Honest current posture

- One-task lane: conditionally ready under supervision for benchmark-eligible work (default path).
- Two-task lane (bounded pilot): ready for a bounded supervised two-task pilot on the curated adjacent-pair corpus, governed by admission, handoff, and role-split truth and measured by conservative canary scorecards and corpus-backed `two_task/bounded_corpus` artifacts.
- Reliability checkpoint (Task 185): conditionally ready under supervision to plan a cautious, bounded capability-widening slice. This does not unblock unattended multi-task autonomy or standalone productization.

This means:

- one-task work remains the default proving path under light supervision,
- the two-task pilot can proceed in a bounded, supervised manner on the curated corpus,
- any widening remains bounded and cautious, based on reliability evidence,
- broad multi-task autonomy is still not justified,
- and the standalone orchestrator-app phase remains blocked behind stronger multi-task autonomy proof.

## Reliability-first continuation checkpoint (Tasks 181–185)

A reliability tranche has been completed with the following evaluation:

- recurring failure-family reduction: evaluated via best-effort deltas when previous reliability snapshots exist; otherwise treated conservatively,
- retry-count improvement: tracked explicitly in the reliability matrix,
- supervision/intervention rate: tracked by lane and normalized by run count,
- compatibility-regression reduction: tracked explicitly and normalized by run count,
- resume-safe recovery behavior: inferred from resume-related failure-family counts; ambiguous signals default to a safe restart posture.

Artifact paths:

- `reliability/one_task_reliability.json`
- `reliability/two_task_reliability.json`
- `reliability/reliability_matrix.json`
- `reliability/reliability_checkpoint.json` (Task 185)

## What still blocks the next phase

Before broad multi-task autonomy or product extraction can be justified, the repo still needs:

- sustained two-task corpus evidence from real bounded pilot runs across curated adjacent-task pairs,
- lower supervised-intervention rates on the bounded pilot lane,
- durable pair-level ledgers that distinguish autonomous progress from operator help,
- additional authority-corroboration truth and failure-family elimination for multi-task sequences beyond the first adjacent pair,
- sharper failure-family classification so repair selection lands on the correct surface more often,
- better resume-safe recovery so partially-successful runs re-enter from precise checkpoints instead of broad retries,
- elimination of repeated docs/status narrative drift,
- and explicit model/output-transport compatibility so Codex-style models do not fail on a GPT-specific file-bundle contract.

## Immediate continuation target (Tasks 186–190)

Run a contract-and-model-compatibility hardening tranche before any cautious widening resumes:

- 186 — docs status headline consistency guard
- 187 — model profile registry and output transport contract declaration
- 188 — Codex patch/apply transport and dual-mode output parsing
- 189 — provider capability negotiation and safe model fallback diagnostics
- 190 — contract and model-transport checkpoint plus cautious next-slice gate

## Operator workflow for the next tranche

Use the next tranche conservatively:

- review merged-main snapshots first,
- plan narrowly from the uploaded source-of-truth files,
- patch docs/tasks/code only as needed,
- validate on a clean branch,
- inspect diffs before merge,
- preserve branch and runtime-artifact hygiene,
- keep all new transport/model compatibility work additive to the proven GPT file-bundle path,
- and do not interpret Codex compatibility as broad autonomy.

Operational reference: `docs/ORCHESTRATOR_CONTRACT_AND_MODEL_COMPAT_186_190.md`

## Next-tranche rationale

The next bottleneck is no longer “prove bounded one-task/two-task exists.” It is “make the repo stop tripping over recurring contract drift.”

Two concrete symptoms now justify this tranche:

- repeated manual cleanup of stale status headlines in `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md`
- a failed `gpt-5-codex` run that reached model output but failed bundle transport because the harness still assumes a strict `FILE:/END_FILE` text bundle contract for all models

The right next move is to harden narrative consistency and model/output-contract compatibility before trying to widen behavior.
