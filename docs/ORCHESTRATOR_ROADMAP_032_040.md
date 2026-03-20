# Orchestrator Roadmap (Tasks 032–041)

## Context

Tasks 015–031 are complete. Task 037 is now also complete and stable on `main`.

The orchestrator now has:

- backlog/state tracking
- review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow
- generic project adapter foundation
- real task execution bridge (task 031 ✅)
- persistent backlog state (task 037 ✅)
- run-loop / CLI / decision-log surface (tasks 038a–038c ✅)
- repo-local import symbol validation (task 038d ✅)

The primary lessons from recent tasks are:

- exact task shape matters as much as the model
- green tests are necessary but not sufficient
- fragile files such as `runner.py` need protected-file rules
- broad tasks should be split into engine, CLI, integration, and hardening phases
- the harness now needs stronger semantic/API awareness, not just stronger format enforcement

## Roadmap summary

| Task | Name | Goal |
|------|------|------|
| 032 | Execution Result Normalization | Stable result contract from raw runner output |
| 033 | Real Review and Compliance Gate | Policy-driven merge readiness |
| 034 | Branch and Worktree Guardrails | Prevent unsafe git state execution |
| 035 | PR Creation Workflow | Automate PR after successful execution |
| 036 | Resume After Approval | Resume from human-approval checkpoints |
| 037 | Persistent Backlog State | Remember task state across runs |
| 038 | Run Loop / CLI / Decision Logging | Add `run_loop()`, CLI surface, and decision journaling |
| 039 | Harness Hardening Tranche | Make `run_task.py` semantically stronger and more reusable |
| 040 | End-to-End Integration Harness | Deterministic full-pipeline tests against the real baseline |
| 041 | Multi-Project Hardening | Remove all TradingBot-specific assumptions |

## Task 039 — Harness Hardening Tranche

**Goal:** Improve `agents/run_task.py` so it can handle a wider variety of tasks safely and with fewer semantic retries.

This tranche is split into:

- **039a — Protected API Semantic Preflight**
  - reject obvious protected API drift before `ruff` / `pytest`
  - detect bad constructor usage, missing methods, and invalid protected imports

- **039b — Machine-Readable Task Contracts**
  - parse structured directives from task specs
  - enforce constructor/method/import/result contracts deterministically

- **039c — Protected Method Edit Engine**
  - unify append-method and replace-method handling
  - keep protected-file edits reliable and reusable

## Task 040 — End-to-End Integration Harness

**Goal:** Add deterministic integration tests for the real orchestrator workflow using the hardened harness and the real current `runner.py` baseline.

**Scope control:** tests only. `runner.py`, `cli.py`, `backlog.py`, and `execution_result.py` are protected.

## Task 041 — Multi-Project Hardening

**Goal:** Remove all hardcoded TradingBot assumptions from the orchestrator engine and prove portability through adapters/config tests.

**Scope control:** `runner.py` and `cli.py` are protected. Work is limited to config/adapter files and tests.

## Cross-task control policy

For all remaining orchestrator tasks:

- prefer one risky production file per task
- use protected-file modes when touching `runner.py`
- reject green-but-policy-violating bundles
- keep optional config access via `getattr(...)`
- keep Windows-compatible subprocess/testing patterns
- prefer machine-readable task contracts where the API surface is fragile

## After task 041

Once 032–041 are complete, the orchestrator can:

- autonomously process a task backlog end to end
- stop safely and resume from approval checkpoints
- work with TradingBot and any future project via config
- enforce protected-file policies more reliably in the harness
- validate protected API contracts earlier and more deterministically

At that point, focus returns to TradingBot product functionality:
- scheduled market-hours execution
- symbol universe management
- backtesting
- live-mode safety gates
