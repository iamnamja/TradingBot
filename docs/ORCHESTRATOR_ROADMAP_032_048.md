# Orchestrator Roadmap (Tasks 032–048)

## Context

Tasks 032–041 are now complete on `main`.

The orchestrator now has:

- backlog/state tracking
- review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow
- generic project adapter foundation
- real task execution bridge
- persistent backlog state
- run-loop / CLI / decision-log surface
- repo-local import symbol validation
- harness semantic hardening
- deterministic end-to-end integration harness
- multi-project config/adapter hardening

The primary lessons from tasks 039–041 are:

- exact task shape matters as much as the model
- green tests are necessary but not sufficient
- fragile files such as `runner.py` and `run_task.py` need narrow scopes
- broad tasks should be split into production-baseline tasks first, then tests-only validation tasks
- the harness is strong enough now that the next leverage is modularity and productization

## Completed roadmap summary

| Task | Name | Status |
|------|------|--------|
| 032 | Execution Result Normalization | ✅ |
| 033 | Real Review and Compliance Gate | ✅ |
| 034 | Branch and Worktree Guardrails | ✅ |
| 035 | PR Creation Workflow | ✅ |
| 036 | Resume After Approval | ✅ |
| 037 | Persistent Backlog State | ✅ |
| 038 | Run Loop / CLI / Decision Logging | ✅ |
| 039 | Harness Hardening Tranche | ✅ |
| 040 | End-to-End Integration Harness | ✅ |
| 041 | Multi-Project Hardening | ✅ |

## Next productization tranche

| Task | Name | Goal |
|------|------|------|
| 042 | Harness Modularization | Split `run_task.py` into reusable modules with zero behavior change |
| 043 | Runtime Artifact Quarantine | Auto-clean known local artifacts while preserving audit visibility |
| 044 | Spec / Execution Two-Phase Workflow | Clarify tasks before execution and run only frozen specs |
| 045 | Structured Failure Journal | Persist classified failures, fingerprints, and remediation history |
| 046 | Project Bootstrap Adapter | Scaffold a new project adapter/config/task template set |
| 047 | Verification Plugins / Validators | Add project-specific validators beyond `ruff` + `pytest` |
| 048 | Safe Parallelism | Parallel execution only for explicitly independent task classes |

## Task 042 — Harness Modularization

**Goal:** Extract `agents/run_task.py` into a thin shell plus reusable modules with no behavior change.

This tranche is split into:

- **042a — Extract Runtime Foundations**
  - move provider execution, git operations, and check execution into dedicated modules

- **042b — Extract Parsers and Policy**
  - move bundle parsing, task-contract parsing, and protected-file policy logic into dedicated modules

- **042c — Extract Semantic Preflight**
  - move semantic/API validation into a dedicated module with parity tests

- **042d — Thin `run_task.py` Shell and Parity**
  - reduce `run_task.py` to orchestration glue and prove behavior parity

## Task 043 — Runtime Artifact Quarantine

**Goal:** Automatically quarantine known runner-local artifacts (for example `last_output.txt`) before final commit/merge while preserving warnings and audit entries.

**Scope control:** focused production task in the harness layer.

## Task 044 — Spec / Execution Two-Phase Workflow

**Goal:** Separate ambiguous-task clarification from implementation.

This tranche is split into:

- **044a — Spec Mode Capture**
  - ask structured clarifying questions when a task is under-specified
  - write a frozen execution-ready spec artifact

- **044b — Frozen Execution Mode**
  - run only against the frozen spec artifact
  - preserve the distinction between planning and implementation

## Task 045 — Structured Failure Journal

**Goal:** Persist raw failure snippets, failure fingerprints, classifications, and chosen remediation paths to improve retries and postmortems.

## Task 046 — Project Bootstrap Adapter

**Goal:** Add a scaffold command that creates a new project adapter/config/task-template set so the orchestrator can be reused outside TradingBot with minimal manual work.

## Task 047 — Verification Plugins / Validators

**Goal:** Support project-specific validators such as:

- CLI smoke checks
- snapshot validators
- schema validators
- API contract validators
- UI screenshot/render validators

without hardcoding them into the core engine.

## Task 048 — Safe Parallelism

**Goal:** Allow parallel execution only for tasks explicitly marked independent and safe.

## Cross-task control policy

For all remaining orchestrator tasks:

- prefer one risky production area per task
- use protected-file modes when touching engine/meta files
- reject green-but-policy-violating bundles
- preserve Windows-compatible subprocess/testing patterns
- prefer tests-only validation tasks after a production baseline lands
- keep raw failure evidence available to the next retry when useful
- never weaken approval policy to gain speed

## After task 048

Once 042–048 are complete, the orchestrator should be ready to:

- run as a reusable product across multiple repositories
- bootstrap new project adapters quickly
- validate project-specific workflows beyond `ruff` + `pytest`
- reduce task-spec patching through spec mode and richer semantic control
- support limited safe parallelism where the task class allows it

At that point, you can either:
- continue using the orchestrator inside the TradingBot repository, or
- split it into its own repository/package with TradingBot as the first client adapter
