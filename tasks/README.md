# Task backlog

Canonical task order for the current orchestrator continuation:

- `068_orchestrator_task_scope_and_split_heuristics.md`
- `069_orchestrator_controller_decomposition_second_extraction.md`
- `070_orchestrator_task_list_manifest_and_queue_model.md`
- `070a_orchestrator_exact_deliverable_parser_and_completion_gate.md`
- `070b_orchestrator_runtime_artifact_retention_and_visibility.md`
- `071_orchestrator_batch_state_persistence_and_resume.md`
- `071a_orchestrator_user_facing_runtime_artifact_retention_switch.md`
- `072_orchestrator_per_task_checkpoint_and_branch_isolation.md`
- `073_orchestrator_batch_failure_policy_and_continue_gate.md`
- `074_orchestrator_batch_runner_cli_and_summary_artifacts.md`
- `075_orchestrator_backlog_execution_end_to_end_proof.md`

Rules:

1. `tasks/README.md` is the canonical visible ordering source.
2. Task markdown filenames and IDs must be referenced exactly as written.
3. If a task enumerates exact deliverables, all listed files must be updated before the task is considered complete.
4. For protected/controller tasks, verify actual branch diffs against task deliverables rather than relying on `_last_agent_patch*` or other scratch artifacts.
