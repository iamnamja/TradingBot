# Docs Index Addendum

## Current roadmap slice

- `ORCHESTRATOR_ROADMAP_186_190.md` — contract and model-compatibility hardening after the post-185 reliability gate
- `ORCHESTRATOR_PHASE_DIRECTION.md` — agreed phase order: one-task truth first, bounded two-task pilot second, reliability hardening next, contract/model compatibility next, cautious capability widening later, standalone app last
- `ORCHESTRATOR_CONTRACT_AND_MODEL_COMPAT_186_190.md` — operator-facing rules, artifact expectations, and working cadence for the 186–190 tranche

## Current continuation note

Tasks 181–185 completed the reliability-first tranche:
- Task 181: failure-family taxonomy and repair-target selection
- Task 182: public/import compatibility guardrails for orchestrator benchmark surfaces
- Task 184: reliability benchmark and regression matrix for one-task and bounded two-task runs
- Task 185: reliability checkpoint and explicit gate for when capability widening may resume

Tasks 186–190 now target the next contract bottlenecks:
- Task 186: docs status headline consistency guard
- Task 187: model profile registry and output transport contract declaration
- Task 188: Codex patch/apply transport and dual-mode output parsing
- Task 189: provider/model capability negotiation and safe fallback diagnostics
- Task 190: contract and model-transport checkpoint plus cautious next-slice gate

## Status guard note

Top-level repo status headlines are now validated by a small, deterministic guard. It checks for headline/task-number consistency across:
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- tranche/index docs that reference the active 186–190 slice

The guard fails on drift; it does not attempt to rewrite docs. See `agents/lib/docs_status_guard.py` and `tests/test_docs_status_guard.py`. Run locally with: `python -m agents.lib.docs_status_guard`. It normalizes hyphen/en-dash variation in ranges and only reports inconsistencies for human follow-up.

## Current next-step note

The near-term focus stays conservative:

- stop repeated docs/status narrative drift
- stop assuming one output contract for every model family
- keep the proven GPT file-bundle path intact while adding Codex-compatible transport additively
- make model/profile incompatibility explicit and diagnosable instead of failing late in bundle transport
- only consider capability widening after the post-190 checkpoint says the model/contract layer is materially more stable

## Explicit model-profile declaration (Task 187)

The harness now declares model/profile transport expectations explicitly:

- Registry: `agents/lib/model_profiles.py` with GPT-style file-bundle (default) and Codex-style patch/apply families.
- Public declaration: `agents.lib.provider_client.declared_transport_contract(...)` returns `model_profile_id`, `output_transport`, and `transport_contract`.

This formalizes the output-transport contract without changing the default proven GPT bundle behavior.

## Task 188 split note

Task 188 has been split into:
- `188a_orchestrator_codex_patch_transport_parser_and_apply_adapter.md`
- `188b_orchestrator_run_task_dual_transport_selection_and_protected_surface_integration.md`

This split keeps the parser/apply adapter work in the normal lane first and defers protected `agents/run_task.py` integration to a separate step.

## Contract and model transport checkpoint (Task 190)

A conservative contract/model-transport checkpoint is now recorded via:
- `src/builder/orchestrator/model_transport_checkpoint.py`
- `reliability/model_transport_checkpoint.json`

The current checkpoint posture remains **conditionally ready under supervision**. This means cautious bounded planning may resume, but unattended multi-task autonomy and standalone productization remain blocked.

