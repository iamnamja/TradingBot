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
- 068–075: backlog execution continuation, merge-readiness hardening, first conservative batch runner, and first narrow end-to-end backlog proof

## Next autonomy and controller-thinning tranche

- **076** `orchestrator_final_acceptance_reviewer_and_report`
- **077** `orchestrator_targeted_self_heal_for_acceptance_failures`
- **078** `orchestrator_batch_executor_loop_and_acceptance_controller`
- **079** `orchestrator_autonomous_pr_merge_and_main_reset_gate`
- **080** `orchestrator_batch_resume_after_merge_and_manual_resolution`
- **081** `orchestrator_controller_decomposition_third_extraction`
- **082** `orchestrator_autonomous_backlog_runner_proof`

## Numbering policy

1. Task IDs and filenames in `tasks/` are the source of truth.
2. Continuation references in docs must use the existing numbered IDs (no ad-hoc renumbering).
3. Umbrella/subtask suffixes (`a`, `b`, etc.) remain part of canonical identity when present.
4. When a plain-number task is deferred behind suffix subtasks, the task index must state that ordering explicitly.

## Related planning artifacts

- `TASK_CLEANUP_055_068.md` tracks cleanup/planning considerations spanning the reliability/autonomy tranche through the stabilization extension.
- `docs/ORCHESTRATOR_ROADMAP_055_068.md` covers the stabilization extension around Task 068.
- `docs/ORCHESTRATOR_ROADMAP_069_075.md` covers the first backlog-execution continuation through the initial proof slice.
- `docs/ORCHESTRATOR_ROADMAP_076_082.md` covers the next autonomy-and-controller-thinning tranche after Task 075.
