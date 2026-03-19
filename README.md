# TradingBot — Task Backlog

This folder is the execution backlog for the TradingBot build. Each task is designed to be:

- small enough to complete in a focused PR
- testable (unit / integration-style tests)
- CI-friendly (`ruff check .` + `pytest -q`)
- compatible with the agent runner workflow (clear inputs/outputs + acceptance criteria)

## Repo conventions (apply to all tasks)

- Source layout: `src/tradingbot/...` (trading bot) and `src/builder/orchestrator/...` (orchestrator)
- Tests: `tests/...`
- Imports in tests:
  - prefer normal package imports: `from tradingbot...` or `from builder.orchestrator...`
  - `tests/conftest.py` already adds `<repo>/src` to `sys.path` on Windows
- Keep modules small and explicit; avoid `import *`.
- Anything that talks to external services must be mockable and must not run in tests by default.

## Agent runner conventions (critical — apply to all orchestrator tasks)

These rules were reinforced by tasks 037–038 and must be embedded in every orchestrator task spec.

### simulate_backlog loop — only valid implementation

```python
while True:
    next_task = self.backlog_tracker.get_next_task([])
    if not next_task:
        break

    processed_tasks.append(next_task.name)
    execution_result = self.execute_task(next_task)
    normalized_result = normalize_execution_result(execution_result)
    result = self.process_execution_result(normalized_result, next_task)

    if result["status"] == "failed":
        stopped_reason = normalized_result.get("failure_text", "Execution failed")
        final_status = "failed"
        break

    if result.get("requires_approval", False):
        approval_required = True
        stopped_reason = "Approval required"
        final_status = "blocked"
        continue

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

- call `get_next_task([])` directly — never call `scan_tasks()` inside the loop
- use `continue` not `break` when approval is required
- append task name to `processed_tasks` BEFORE any break/continue check

### run_review — empty changed_files

When `changed_files` is empty on the legacy/mock path: return `{"mergeable": True}`.
Never return `{"mergeable": False}` solely because `changed_files` is empty.

### ProjectConfig — always mutable

Never use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.
Always use `getattr(self.config, "field_name", default)` for optional config fields.

### Legacy success contract — never change these

- `status == "running"` (not `"succeeded"`)
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`

### Failure message format

- `message == "Execution failed: {failure_text}"` when failure_text or stderr is present
- read from `execution_result.get("failure_text") or execution_result.get("stderr") or ""`

### Protected-file modes

Task specs may now declare one of these narrow scopes:

- `EXACT_COPY_PLUS_APPEND_METHOD`
- `METHOD_ADD_ONLY`
- `TESTS_ONLY`
- `CONFIG_ONLY`
- `DOCS_ONLY`

If a task marks a file as protected, green tests are not enough — the task is still invalid if the protected-file rule is violated.

### Task shaping rule

When a task touches a fragile, high-contract file such as `runner.py`, prefer the smallest safe unit of change:

- one risky production file per task
- CLI wiring separated from runner changes
- integration harness separated from core contract changes
- config/adapters separated from engine changes

### Windows compatibility

- never use `echo` as a subprocess command in tests
- use `sys.executable + ["-c", "..."]` for cross-platform subprocess tests
- never patch `subprocess.run` while calling `run_next_task()` under a config where `task_runner_command is None`

## Environment recommendations

For OpenAI GPT-5 task runs, keep these in `.env`:

```env
TRADINGBOT_OPENAI_TIMEOUT=900
TRADINGBOT_OPENAI_RETRIES=2
```

Always use explicit provider/model flags when running agent tasks.

## How to run checks locally

```powershell
py -m pip install -r requirements.txt
ruff check .
pytest -q
```

## How to run a task

```powershell
py agents/run_task.py tasks/038_orchestrator_run_loop_cli.md --push --provider openai --model gpt-5
```

## How to clean up after a failed task run

```powershell
git switch main
git fetch origin
git reset --hard origin/main
git clean -fd
git branch -D agent-{task-branch-name}
git status
```

## How to merge a fix manually and re-run

```powershell
git switch -c fix/description
git add path/to/fixed/file
git commit -m "fix: description"
git push -u origin fix/description
gh pr create --base main --head fix/description --fill
gh pr merge --merge --auto --delete-branch

git switch main
git fetch origin
git reset --hard origin/main
git clean -fd
py agents/run_task.py tasks/NNN_task_name.md --push --provider openai --model gpt-5
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
18. `038_orchestrator_run_loop_cli` — now scoped to engine-only `run_loop()`
19. `039_orchestrator_end_to_end_integration_harness` — CLI wiring + end-to-end harness
20. `040_orchestrator_multi_project_hardening`
