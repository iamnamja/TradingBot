# Docs Index Addendum

## Current roadmap slice

- `ORCHESTRATOR_ROADMAP_186_190.md` — contract and model-compatibility hardening after the post-185 reliability gate
- `ORCHESTRATOR_PHASE_DIRECTION.md` — agreed phase order: one-task truth first, bounded two-task pilot second, reliability hardening next, contract/model compatibility next, cautious capability widening later, standalone app last
- `ORCHESTRATOR_CONTRACT_AND_MODEL_COMPAT_186_190.md` — operator-facing rules, artifact expectations, and working cadence for the 186–190 tranche

## Current continuation note

Tasks 181–185 completed the reliability-first tranche:
- Task 181: failure-family taxonomy and repair-target selection
- Task 182: public/import compatibility guardrails for orchestrator benchmark surfaces
- Task 183: resume-safe attempt checkpoint and recovery re-entry truth
- Task 184: reliability benchmark and regression matrix for one-task and bounded two-task runs
- Task 185: reliability checkpoint and explicit gate for when capability widening may resume

Tasks 186–190 now target the next contract bottlenecks:
- Task 186: docs status headline consistency guard
- Task 187: model profile registry and output transport contract declaration
- Task 188: Codex patch/apply transport and dual-mode output parsing
- Task 189: provider/model capability negotiation and safe fallback diagnostics
- Task 190: contract and model-transport checkpoint plus cautious next-slice gate

## Current next-step note

The near-term focus stays conservative:

- stop repeated docs/status narrative drift
- stop assuming one output contract for every model family
- keep the proven GPT file-bundle path intact while adding Codex-compatible transport additively
- make model/profile incompatibility explicit and diagnosable instead of failing late in bundle transport
- only consider capability widening after the post-190 checkpoint says the model/contract layer is materially more stable

The immediate operator-facing reference for this slice is `ORCHESTRATOR_CONTRACT_AND_MODEL_COMPAT_186_190.md`.
