# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 124**.

The deterministic proof-backed slice currently covers:

- role-separated **controller / builder / verifier** contract
- sequential role loop with controller-owned final continue/stop authority
- bounded supervised local-first **multi-project portfolio slice** across more than one registered project
- project-scoped workspace/branch/state/carry-forward memory isolation
- explicit backlog + dependency-truth next-task selection posture
- bounded self-heal/repair planning with conservative rollback posture
- project-aware validation matrices and authority profiles
- hosted-authority convergence + merge-eligibility truth with conservative stop gating
- extraction-prep consumer boundary posture (not full extraction)

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for authoritative status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded supervised multi-project slice:

1. controller/builder/verifier role separation
2. project selection across more than one registered project
3. isolated project state/branch/workspace/carry-forward memory namespaces
4. dependency-aware next-task choice
5. bounded repair planning and rollback-conservative posture
6. project-aware authority evaluation with conservative stop when unsatisfied
7. explicit claim discipline bound to local deterministic tests

It does **not** claim:

- broad unattended scheduler autonomy
- arbitrary protected/controller/meta task-family autonomy
- full standalone extraction completion
- arbitrary language portability

## Next continuation target

Task 124 freezes the public/tested compatibility surface so future orchestrator repairs preserve aliases and stable payload keys instead of renaming seams ad hoc.
