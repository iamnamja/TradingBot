# Tasks Index (Canonical)

This file is the canonical visible ordering for task execution history and continuation planning.

## Completed foundation and buildout

- 001–014: TradingBot runtime foundation and paper-cycle features
- 015–038 family: Orchestrator state, policy, execution, review, guardrails, resume, persistence, and run-loop surfaces
- 039–043 family: Harness hardening, protected-edit/semantic checks, modularization, artifact quarantine
- 044–048 family: Spec execution lanes, failure journaling context, bootstrap adapters, validator plugins, safe parallelism
- 049–050: Shell convergence umbrella and public interface freeze
- 051–054 (+054a/054b): Docs normalization, portability proof, seam registry, seam-lint and harness gate extensions
- 055–060: Reliability/autonomy tranche

## Continuation reset and active deferred sequence

- **061** `orchestrator_continuation_reset_and_numbering_sync`  
  Documentation/task-order realignment checkpoint after reliability/autonomy completion.

- **062** `orchestrator_integrated_capabilities_e2e`
- **063** `orchestrator_failure_journal_live_seam`
- **064** `orchestrator_safe_parallelism_review_integration`
- **065** `orchestrator_runtime_artifact_quarantine_integration`
- **066** `orchestrator_package_extraction_prep`
- **067** `orchestrator_canonical_docs_path_policy`
- **068** `orchestrator_task_scope_and_split_heuristics`

## Numbering policy

1. Task IDs and filenames in `tasks/` are the source of truth.
2. Continuation references in docs must use the existing numbered IDs (no ad-hoc renumbering).
3. Umbrella/subtask suffixes (`a`, `b`, etc.) remain part of canonical identity when present.

## Related planning artifact

- `TASK_CLEANUP_055_068.md` tracks cleanup/planning considerations spanning the reliability/autonomy tranche through the deferred continuation window.
