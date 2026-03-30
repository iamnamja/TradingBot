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
- 068a–068c: stabilization extension for protected/controller execution and controller thinning
- 068: original task-scope/split heuristics confirmed after the stabilization extension
- 069: controller decomposition second extraction
- 070: task-list manifest and queue model groundwork

## Immediate stabilization follow-ons before resumed backlog continuation

- **070a** `orchestrator_exact_deliverable_parser_and_completion_gate`
- **070b** `orchestrator_runtime_artifact_retention_and_visibility`

## Backlog execution continuation

- **071** `orchestrator_batch_state_persistence_and_resume`
- **072** `orchestrator_per_task_checkpoint_and_branch_isolation`
- **073** `orchestrator_batch_failure_policy_and_continue_gate`
- **074** `orchestrator_batch_runner_cli_and_summary_artifacts`
- **075** `orchestrator_backlog_execution_end_to_end_proof`

## Numbering policy

1. Task IDs and filenames in `tasks/` are the source of truth.
2. Continuation references in docs must use the existing numbered IDs (no ad-hoc renumbering).
3. Umbrella/subtask suffixes (`a`, `b`, etc.) remain part of canonical identity when present.
4. When a plain-number task is deferred behind suffix subtasks (for example `068a–068c` before `068`, or `070a/070b` before `071`), the task index must state that ordering explicitly.

## Related planning artifacts

- `TASK_CLEANUP_055_068.md` tracks cleanup/planning considerations spanning the reliability/autonomy tranche through the stabilization extension.
- `docs/ORCHESTRATOR_ROADMAP_055_068.md` covers the stabilization extension around Task 068.
- `docs/ORCHESTRATOR_ROADMAP_069_075.md` covers the backlog-execution continuation beginning at 069, including the 070a/070b stabilization follow-ons before 071.
