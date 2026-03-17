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
- `tests/test_project_adapter.py`
- `tests/test_multi_project_adapters.py`

All five files must be materially updated in the same bundle.


## CRITICAL — runner.py is PROTECTED and must NOT be included as a deliverable

`src/builder/orchestrator/runner.py` is a stable, fully-tested file. Do NOT include it in the bundle.
Do NOT rewrite it. Do NOT modify it. Do NOT include it as a deliverable.

If this task requires new functionality in runner.py, add ONLY the specific new method described,
using surgical `str_replace`-style additions. All existing methods must remain exactly unchanged.

The agent must NOT regenerate runner.py from scratch under any circumstances.

## Bundle completeness requirement

The bundle is incomplete unless all listed deliverables are present.

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

## CRITICAL — process_execution_result must be implemented exactly

Do NOT simplify `process_execution_result`. Route through `FailureClassifier`, `RepairWorkflow`, and audit log calls.

### Review blocked path must return exactly:
```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "review_blocked",
    "next_action": "requires_approval",   # NOT "review", "merge", or anything else
    "requires_approval": True,
}
```

### Failure path must return:
```python
{
    "task_name": task.name,
    "status": "failed",
    "message": f"Execution failed: {failure_text}" if failure_text else "Execution failed.",
    "outcome": "repair_required",
    "next_action": next_action,           # from repair_action, fallback "require_human_review"
    "requires_approval": repair_action.get("requires_approval", True),  # True by default
}
```

Do NOT return `"Task execution failed."` or any other message format.
Do NOT return `requires_approval: False` on the failure path.
Do NOT skip `FailureClassifier` or `RepairWorkflow`.

### Required imports in runner.py — do not remove any:
```python
from .approval import create_approval_checkpoint
from .audit import (
    log_approval_checkpoint,
    log_classification_result,
    log_repair_decision,
    log_review_verdict,
    log_selected_task,
)
from .execution_result import normalize_execution_result
from .failures import FailureClassifier
from .repair import RepairWorkflow
```

## CRITICAL — stopped_reason contract

When backlog completes normally: `stopped_reason == ""` (empty string). NEVER `"All tasks completed"` or any other non-empty value.

Only non-empty values allowed:
- `"Execution failed"` on task failure
- `"Approval required"` when approval is needed

## CRITICAL — simulate_backlog with normalization

Must call `normalize_execution_result` before `process_execution_result`:

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
        continue  # MUST be continue, NOT break

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

## CRITICAL — run_next_task normalization

Must call `normalize_execution_result` between `execute_task` and `process_execution_result`:

```python
execution_result = self.execute_task(running_task)
normalized_result = normalize_execution_result(execution_result)
return self.process_execution_result(normalized_result, running_task)
```

## CRITICAL — execute_task default mock return

When `task_runner_command` is None, return exactly:
```python
{
    "success": True,
    "output": "Task executed successfully",
    "changed_files": ["file1.py"],
}
```

Do NOT return `{"success": True, "changed_files": []}` — the empty list causes test failures.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.

Correct:
```python
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.policy import PolicyEngine
```

Invalid (breaks CI):
```python
from src.builder.orchestrator.runner import OrchestratorRunner
```
