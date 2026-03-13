# Task 040 — Multi-Project Hardening

## Goal

Remove all hidden project-specific assumptions from the orchestrator so it works correctly with any project configuration, not just TradingBot.

## Why

The orchestrator currently has implicit assumptions about TradingBot's directory layout, file patterns, and runner command. These must become fully configurable so the same orchestrator code can drive any project.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `ProjectAdapter.get_tradingbot_default_config()` must still exist and work
- `ProjectAdapter.get_generic_project_config()` must still exist and work
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `src/builder/orchestrator/runner.py`
- `tests/test_project_adapter.py`
- `tests/test_multi_project_adapters.py`

All five files must be materially updated in the same bundle.

## Bundle completeness requirement

The bundle is incomplete unless all five deliverables are present.

## Critical anti-truncation rule

`src/builder/orchestrator/runner.py` must visibly contain all of these method headers:

- `def select_next_task(`
- `def run_next_task(`
- `def execute_task(`
- `def process_execution_result(`
- `def simulate_backlog(`

And must contain a `simulate_backlog` return dict with all five keys:
`processed_tasks`, `stopped_reason`, `final_status`, `approval_required`, `planned_actions`

## Required behavior

### project_config.py

`ProjectConfig` must support these configurable fields (all optional with safe defaults):

```python
@dataclass  # NOT frozen
class ProjectConfig:
    tasks_directory: str
    lint_command: str
    test_command: str
    branch_naming_pattern: str
    protected_file_patterns: list[str]
    artifact_path_patterns: list[str]
    approval_required_file_patterns: list[str]
    task_runner_command: str | None = None   # optional real runner
    state_path: str | None = None            # optional state file path
    task_file_pattern: str = "*.md"          # configurable task file glob
    audit_path: str | None = None            # optional audit log path
```

Do NOT use `@dataclass(frozen=True)`. All fields must be mutable after construction.

### project_adapter.py

`ProjectAdapter.get_tradingbot_default_config()` must return a `ProjectConfig` with:
- `task_runner_command = None`
- `state_path = None`
- all existing fields preserved

`ProjectAdapter.get_generic_project_config()` must return a `ProjectConfig` with:
- `task_runner_command = None`
- `state_path = None`
- generic/neutral values for all fields

Both factory methods must remain on `ProjectAdapter` — do NOT move them to `ProjectConfig`.

### runner.py

All config field access that might not exist on older configs must use `getattr` with a safe default:

```python
# Good
task_runner_command = getattr(self.config, "task_runner_command", None)
state_path = getattr(self.config, "state_path", "tasks/state.json")
task_file_pattern = getattr(self.config, "task_file_pattern", "*.md")
audit_path = getattr(self.config, "audit_path", None)
```

Never access config fields directly if they might not exist on all ProjectConfig variants.

## Exact legacy contract that must not be changed

When a pending task exists on the legacy/mock success path:
- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`
- `requires_approval == False`

When review is blocked:
- `status == "running"`
- `message == "Task is now running."`
- `requires_approval == True`
- `outcome == "review_blocked"`

When no pending task:
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`

When execution fails:
- `status == "failed"`
- `outcome == "repair_required"`
- `next_action == "require_human_review"`

## CRITICAL — simulate_backlog must be implemented exactly

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

## CRITICAL — run_review behavior

When `changed_files` is empty on the legacy/mock success path, return `{"mergeable": True}`.

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or `GenericProjectConfig`.
Do NOT mix frozen and non-frozen dataclasses.

The following must work after construction:
```python
config = ProjectAdapter.get_tradingbot_default_config()
config.task_runner_command = "python"
config.state_path = "tasks/state.json"
```

## Exact forbidden patterns

- `@dataclass(frozen=True)` on any config class
- hardcoded TradingBot-specific paths or patterns in orchestrator core
- moving factory methods from `ProjectAdapter` to `ProjectConfig`
- direct attribute access on config without `getattr` for optional fields
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- unused local variables that ruff will flag

## Multi-project test requirements

`tests/test_multi_project_adapters.py` must demonstrate the orchestrator working with at least two distinct project configurations:

1. TradingBot config (existing)
2. A second generic/hypothetical project config with different:
   - `tasks_directory`
   - `branch_naming_pattern`
   - `task_file_pattern`
   - `lint_command`
   - `test_command`

Tests must verify that `OrchestratorRunner` works correctly with both configs.

## Acceptance criteria

- `get_tradingbot_default_config()` returns config with `task_runner_command == None`
- `get_generic_project_config()` returns config with `task_runner_command == None`
- Config fields are mutable after construction
- All optional fields accessible via `getattr` without AttributeError
- At least two distinct project configs tested end-to-end
- No hardcoded project assumptions in orchestrator core

`ruff check .` must pass. `pytest -q` must be fully green.
