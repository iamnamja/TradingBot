# Orchestrator Roadmap (Tasks 032–040)

## Context

Tasks 015–031 are complete. The orchestrator now has:
- backlog/state tracking
- review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow
- generic project adapter foundation
- real task execution bridge (task 031 ✅)

The agent model is now **Claude Sonnet** (switched from GPT-4o-mini in task 031). Claude produces green results in 1 iteration when task specs are precise.

## Roadmap summary

| Task | Name | Goal |
|------|------|------|
| 032 | Execution Result Normalization | Stable result contract from raw runner output |
| 033 | Real Review and Compliance Gate | Policy-driven merge readiness |
| 034 | Branch and Worktree Guardrails | Prevent unsafe git state execution |
| 035 | PR Creation Workflow | Automate PR after successful execution |
| 036 | Resume After Approval | Resume from human-approval checkpoints |
| 037 | Persistent Backlog State | Remember task state across runs |
| 038 | Run Loop CLI | Continuous task processing loop |
| 039 | End-to-End Integration Harness | Full pipeline integration test |
| 040 | Multi-Project Hardening | Remove all TradingBot-specific assumptions |

## Task 032 — Execution Result Normalization

**Goal:** Build a normalization layer in `execution_result.py` that converts raw runner output into a stable dict used by the rest of the orchestrator.

**Key outputs:**
- `src/builder/orchestrator/execution_result.py` with `normalize_execution_result(raw) -> dict`
- Updated `runner.py` that calls normalization before `process_execution_result`
- Tests covering: success, lint failure, missing deliverables, malformed output, unknown fallback

**Why first:** All downstream tasks depend on a stable execution result shape.

## Task 033 — Real Review and Compliance Gate

**Goal:** Evaluate actual execution results and changed files through a `PolicyEngine` before allowing merge readiness.

**Key outputs:**
- `src/builder/orchestrator/policy.py` with `PolicyEngine` class
- Updated `review.py` using `PolicyEngine`
- Tests covering: mergeable, missing deliverables, approval-required files, no-files edge case

**Why here:** Depends on normalized execution results from 032.

## Task 034 — Branch and Worktree Guardrails

**Goal:** Block real execution on `main`, dirty worktrees, or mismatched branch names. Simulation always bypasses guardrails.

**Key outputs:**
- `src/builder/orchestrator/git_guardrails.py` with `GitGuardrails` class
- Updated `runner.py` calling guardrails before real execution
- Tests: blocked on main, blocked on dirty worktree, passes on valid branch, simulation bypass

## Task 035 — PR Creation Workflow

**Goal:** Automate PR creation after successful execution that passes review. PR creation is opt-in and never runs in dry-run or simulate mode.

**Key outputs:**
- `src/builder/orchestrator/command_runner.py` — safe subprocess abstraction
- `src/builder/orchestrator/merge.py` with `PRCreator` class
- `runner.py` result includes `pr_attempted` and `pr_success` keys

## Task 036 — Resume After Approval

**Goal:** Resume execution from a human-approved checkpoint rather than restarting from scratch.

**Key outputs:**
- `approval.py` additions: `load_approval_checkpoint`, `grant_approval`, `is_approval_granted`
- `runner.py` `resume_from_approval()` method
- `cli.py` `--resume` flag

## Task 037 — Persistent Backlog State

**Goal:** Persist task execution state to `tasks/state.json` between runs. Completed tasks are skipped. Simulation never writes state.

**Key outputs:**
- `state.py` with `save()` and `load()` methods
- `backlog.py` with `update_task_status()` method
- `runner.py` reading/writing state on each execution

## Task 038 — Run Loop CLI

**Goal:** Add a `run_loop()` method and CLI modes (`run-once`, `run-loop`, `simulate`, `resume`) for continuous task processing.

**Key outputs:**
- `runner.py` `run_loop()` method calling `run_next_task()` internally
- `cli.py` with four modes and structured summary output

## Task 039 — End-to-End Integration Harness

**Goal:** Single integration test covering the full pipeline: discovery → execution → normalization → review → approval → PR readiness.

**Key outputs:**
- `tests/test_orchestrator_end_to_end.py` with 5 scenarios
- All external calls mocked (subprocess, git, GitHub CLI)
- Windows-compatible, deterministic

## Task 040 — Multi-Project Hardening

**Goal:** Remove all hardcoded TradingBot assumptions from the orchestrator engine. Make the orchestrator work with any project via config.

**Key outputs:**
- `ProjectConfig` with all fields configurable: `task_file_pattern`, `state_path`, `audit_path`, `task_runner_command`
- Tests proving orchestrator works with two distinct project configs
- All optional config fields accessed via `getattr` everywhere in runner

## After task 040

Once 032–040 are complete, the orchestrator can:
- autonomously process a task backlog end-to-end
- stop safely and resume from approval checkpoints
- work with TradingBot and any future project via config

At that point, focus returns to TradingBot product functionality:
- scheduled market-hours execution
- symbol universe management
- backtesting
- live-mode safety gates
