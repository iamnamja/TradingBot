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
- 076–082: autonomous backlog progression and controller-thinning continuation, ending with the first narrow ordinary-manifest autonomous proof slice
- 083–089: controller-contract hardening, stricter controller-task discipline, and the hardened short-manifest proof synchronization

## Next multi-agent portability and productization tranche

- **090** `orchestrator_multi_agent_role_contract_and_handoff_state`
- **091** `orchestrator_builder_verifier_controller_loop`
- **092** `orchestrator_verification_authority_and_ci_required_checks`
- **093** `orchestrator_repair_strategy_router_and_failure_lane_selection`
- **094** `orchestrator_project_workspace_adapter_and_bootstrap_contract_v2`
- **095** `orchestrator_dependency_aware_manifest_planner`
- **096** `orchestrator_task_family_router_and_agent_selection`
- **097** `orchestrator_second_project_multi_agent_portability_proof`
- **098** `orchestrator_standalone_package_boundary_and_consumer_bridge`
- **099** `orchestrator_multi_agent_portability_proof_sync`

## Numbering policy

1. Task IDs and filenames in `tasks/` are the source of truth.
2. Continuation references in docs must use the existing numbered IDs (no ad hoc renumbering).
3. Umbrella/subtask suffixes (`a`, `b`, etc.) remain part of canonical identity when present.
4. When a plain-number task is deferred behind suffix subtasks, the task index must state that ordering explicitly.

## Related planning artifacts

- `TASK_CLEANUP_055_068.md` tracks cleanup/planning considerations spanning the reliability/autonomy tranche through the stabilization extension.
- `docs/ORCHESTRATOR_ROADMAP_055_068.md` covers the stabilization extension around Task 068.
- `docs/ORCHESTRATOR_ROADMAP_069_075.md` covers the first backlog-execution continuation through the initial proof slice.
- `docs/ORCHESTRATOR_ROADMAP_076_082.md` covers the autonomy-and-controller-thinning tranche that culminated in Task 082.
- `docs/ORCHESTRATOR_ROADMAP_083_089.md` covers the controller-contract hardening tranche after Task 082.
- `docs/ORCHESTRATOR_ROADMAP_090_099.md` covers the next multi-agent portability and productization tranche after Task 089.
