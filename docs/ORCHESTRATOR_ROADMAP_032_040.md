# Orchestrator Roadmap (Tasks 032–040)

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

The primary lessons from tasks 037–038 are:

- exact task shape matters as much as the model
- green tests are necessary but not sufficient
- fragile files such as `runner.py` need protected-file rules
- broad tasks should be split into engine, CLI, and integration phases

## Roadmap summary

| Task | Name | Goal |
|------|------|------|
| 032 | Execution Result Normalization | Stable result contract from raw runner output |
| 033 | Real Review and Compliance Gate | Policy-driven merge readiness |
| 034 | Branch and Worktree Guardrails | Prevent unsafe git state execution |
| 035 | PR Creation Workflow | Automate PR after successful execution |
| 036 | Resume After Approval | Resume from human-approval checkpoints |
| 037 | Persistent Backlog State | Remember task state across runs |
| 038 | Run Loop Engine | Add `run_loop()` safely on top of `run_next_task()` |
| 039 | CLI Wiring and End-to-End Harness | Wire CLI modes and deterministic full-pipeline tests |
| 040 | Multi-Project Hardening | Remove all TradingBot-specific assumptions |

## Task 032 — Execution Result Normalization

**Goal:** Build a normalization layer in `execution_result.py` that converts raw runner output into a stable dict used by the rest of the orchestrator.

## Task 033 — Real Review and Compliance Gate

**Goal:** Evaluate actual execution results and changed files through a `PolicyEngine` before allowing merge readiness.

## Task 034 — Branch and Worktree Guardrails

**Goal:** Block real execution on `main`, dirty worktrees, or mismatched branch names. Simulation always bypasses guardrails.

## Task 035 — PR Creation Workflow

**Goal:** Automate PR creation after successful execution that passes review. PR creation is opt-in and never runs in dry-run or simulate mode.

## Task 036 — Resume After Approval

**Goal:** Resume execution from a human-approved checkpoint rather than restarting from scratch.

## Task 037 — Persistent Backlog State ✅

**Goal:** Persist task execution state to `tasks/state.json` between runs. Completed tasks are skipped. Simulation never writes state.

**Status:** Completed manually after constraining the task and preserving the green `runner.py` baseline.

## Task 038 — Run Loop Engine

**Goal:** Add a `run_loop()` method to `runner.py` that repeatedly calls `run_next_task()`.

**Scope control:** `runner.py` is in protected additive mode. No CLI work in this task.

## Task 039 — CLI Wiring and End-to-End Harness

**Goal:** Wire `cli.py` to expose `run-once`, `run-loop`, `simulate`, and `resume`, then add deterministic integration tests for the full pipeline.

**Scope control:** `runner.py` is protected. Production changes are limited to `cli.py`.

## Task 040 — Multi-Project Hardening

**Goal:** Remove all hardcoded TradingBot assumptions from the orchestrator engine and prove portability through adapters/config tests.

**Scope control:** `runner.py` and `cli.py` are protected. Work is limited to config/adapter files and tests.

## Cross-task control policy

For all remaining orchestrator tasks:

- prefer one risky production file per task
- use protected-file modes when touching `runner.py`
- reject green-but-policy-violating bundles
- keep optional config access via `getattr(...)`
- keep Windows-compatible subprocess/testing patterns

## After task 040

Once 032–040 are complete, the orchestrator can:

- autonomously process a task backlog end to end
- stop safely and resume from approval checkpoints
- work with TradingBot and any future project via config
- enforce protected-file policies more reliably in the harness

At that point, focus returns to TradingBot product functionality:
- scheduled market-hours execution
- symbol universe management
- backtesting
- live-mode safety gates
