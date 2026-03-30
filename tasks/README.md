# Tasks Index (Canonical)

This file is the canonical visible ordering for task execution history and continuation planning.

## Completed foundation and buildout

- 001–014: TradingBot runtime foundation and paper-cycle features
- 015–038 family: Orchestrator state, policy, execution, review, guardrails, resume, persistence, and run-loop surfaces
- 039–043 family: Harness hardening, protected-edit/semantic checks, modularization, artifact quarantine
- 044–048 family: Spec execution lanes, failure journaling context, bootstrap adapters, validator plugins, safe parallelism
- 049–050: Shell convergence umbrella and public interface freeze
- 051–054 (+054a/054b): Docs normalization, portability proof, seam registry, seam-lint and harness gate extensions
- 055–067 (+065a, 067a): Reliability/autonomy continuation and follow-on control-plane hardening

## Stabilization extension before Task 068

- **068a** `orchestrator_protected_lane_execution_hardening`
- **068b** `orchestrator_duplicate_bundle_normalization_and_repair`
- **068c** `orchestrator_controller_decomposition_and_first_extraction`

## Deferred continuation after the stabilization extension

- **068** `orchestrator_task_scope_and_split_heuristics`

## Numbering policy

1. Task IDs and filenames in `tasks/` are the source of truth.
2. Continuation references in docs must use the existing numbered IDs (no ad-hoc renumbering).
3. Umbrella/subtask suffixes (`a`, `b`, etc.) remain part of canonical identity when present.
4. When a plain-number task is deferred behind suffix subtasks (for example `068a–068c` before `068`), the task index must state that ordering explicitly.

## Related planning artifacts

- `TASK_CLEANUP_055_068.md` tracks cleanup/planning considerations spanning the reliability/autonomy tranche through the current continuation window.
- `docs/ORCHESTRATOR_ROADMAP_055_068.md` is the active roadmap for the stabilization extension.
