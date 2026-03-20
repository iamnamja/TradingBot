# TradingBot — Task Backlog

This folder is the execution backlog for the TradingBot build. Each task is designed to be:

- Small enough to complete in a focused PR
- Testable (unit / integration-style tests)
- CI-friendly (`ruff check .` + `pytest -q`)
- Compatible with the agent runner workflow (clear inputs/outputs + acceptance criteria)

## Repo conventions (apply to all tasks)

- Source layout: `src/tradingbot/...` (trading bot) and `src/builder/orchestrator/...` (orchestrator)
- Tests: `tests/...`
- Imports in tests:
  - Prefer normal package imports: `from tradingbot...` or `from builder.orchestrator...`
  - `tests/conftest.py` already adds `<repo>/src` to `sys.path` on Windows
- Keep modules small and explicit; avoid "magic" imports and `import *`.
- Anything that talks to external services **must** be mockable and must not run in tests by default.

## Agent runner conventions (critical — apply to all orchestrator tasks)

These rules were learned from task 031 and must be embedded in every orchestrator task spec:

### simulate_backlog loop — only valid implementation

```python
while True:
    next_task = self.backlog_tracker.get_next_task([])
    if not next_task:
        break

    processed_tasks.append(next_task.name)
    execution_result = self.execute_task(next_task)
    result = self.process_execution_result(execution_result, next_task)

    if result["status"] == "failed":
        stopped_reason = execution_result.get("failure_text", "Execution failed")
        final_status = "failed"
        break

    if result.get("requires_approval", False):
        approval_required = True
        stopped_reason = "Approval required"
        final_status = "blocked"
        continue  # MUST be continue, NOT break

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

- Call `get_next_task([])` directly — NEVER call `scan_tasks()` inside the loop
- Use `continue` not `break` when approval is required
- Append task name to `processed_tasks` BEFORE any break/continue check

### run_review — empty changed_files

When `changed_files` is empty on the legacy/mock path: return `{"mergeable": True}`.
Never return `{"mergeable": False}` solely because `changed_files` is empty.

### ProjectConfig — always mutable

Never use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.
Always use `getattr(self.config, "field_name", default)` for optional config fields.

### Legacy success contract — never change these

- `status == "running"` (not "succeeded")
- `message == "Task is now running."` (not "Execution succeeded.")
- `outcome == "ready_for_pr"`
- `next_action == "merge"`

### Failure message format

- `message == "Execution failed: {failure_text}"` when failure_text or stderr is present
- Read from `failure_text` OR `stderr` key: `execution_result.get("failure_text") or execution_result.get("stderr") or ""`

### Windows compatibility

- Never use `echo` as a subprocess command in tests — not portable on Windows PowerShell
- Use `sys.executable + ["-c", "..."]` for cross-platform subprocess tests
- Never patch `subprocess.run` while calling `run_next_task()` under a config where `task_runner_command is None`

## How to run checks locally

```powershell
py -m pip install -r requirements.txt
ruff check .
pytest -q
```

## How to run a task

```powershell
py agents/run_task.py tasks/032_orchestrator_execution_result_normalization.md --push
```

## How to clean up after a failed task run

```powershell
git switch main
git branch -D agent-{task-branch-name}
git reset --hard HEAD
git clean -fd
git status  # should say: nothing to commit, working tree clean
```

## How to merge a fix manually and re-run

```powershell
# create fix branch, commit, PR, merge
git switch -c fix/description
git add path/to/fixed/file
git commit -m "fix: description"
git push -u origin fix/description
gh pr create --base main --head fix/description --fill
gh pr merge --merge --auto --delete-branch

# switch back to clean main and run
git switch main
git fetch origin
git reset --hard origin/main
git clean -fd
py agents/run_task.py tasks/NNN_task_name.md --push
```

## Task Order

### Trading Bot (core product)

1. `001_project_structure`
2. `002_config_settings`
3. `003_market_hours_guard` ✅
4. `004_data_layer`
5. `005_indicators`
6. `006_strategy_v1`
7. `007_llm_advisor`
8. `008_risk_gate`
9. `009_execution_engine`
10. `010_e2e_cycle_logging`

### Orchestrator (agent framework)

11. `031_orchestrator_real_task_execution` ✅
12. `032_orchestrator_execution_result_normalization`
13. `033_orchestrator_real_review_and_compliance_gate`
14. `034_orchestrator_branch_and_worktree_guardrails`
15. `035_orchestrator_pr_creation_workflow`
16. `036_orchestrator_resume_after_approval`
17. `037_orchestrator_persistent_backlog_state` ✅
18. `038_orchestrator_run_loop_cli` ✅
19. `039_orchestrator_harness_hardening_umbrella` (do not run directly)
20. `039a_orchestrator_protected_api_semantic_preflight`
21. `039b_orchestrator_machine_readable_task_contracts`
22. `039c_orchestrator_protected_method_edit_engine`
23. `040_orchestrator_end_to_end_integration_harness`
24. `041_orchestrator_multi_project_hardening` (do not run directly)
25. `041a_orchestrator_project_config_schema`
26. `041b_orchestrator_multi_project_adapter_tests`
