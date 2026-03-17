# Task 035 — PR Creation Workflow

## Goal

Allow the orchestrator to create a GitHub PR after successful task execution that passes review and policy checks.

## Why

After execution succeeds and review passes, the orchestrator should automate PR creation rather than requiring manual intervention for every task.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged — do NOT add `create_pr=` parameter
- `simulate_backlog()` signature and return contract unchanged

PR creation must be opt-in and must not run in dry_run or simulate mode.

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/merge.py`
- `src/builder/orchestrator/command_runner.py`
- `tests/test_orchestrator_pr_creation_workflow.py`

All four files must be materially updated in the same bundle.

## Bundle completeness requirement

The bundle is incomplete unless all four deliverables are present.

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

### command_runner.py

Must define a `CommandRunner` class for executing shell commands safely:

```python
class CommandRunner:
    def run(self, cmd: list[str], capture: bool = True) -> dict[str, Any]: ...
```

Returns:
```python
{
    "success": bool,
    "stdout": str,
    "stderr": str,
    "returncode": int,
}
```

Must be mockable in tests — do not use subprocess directly in caller code.

### merge.py

Must define a `PRCreator` class:

```python
class PRCreator:
    def __init__(self, command_runner: CommandRunner) -> None: ...
    def create_pr(self, branch: str, title: str, body: str) -> dict[str, Any]: ...
```

`create_pr` must use `gh pr create` via `CommandRunner`.

Returns:
```python
{
    "pr_attempted": bool,
    "pr_success": bool,
    "pr_url": str,
    "error": str,
}
```

### runner.py integration

`run_next_task()` result must include:
```python
{
    "pr_attempted": bool,
    "pr_success": bool,
}
```

PR creation must only run when ALL of these are true:
- execution succeeded
- review is mergeable
- `requires_approval == False`
- `dry_run == False`

PR must NOT be attempted when:
- dry_run is True
- review is blocked
- approval is required

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

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

## Exact forbidden patterns

- adding `create_pr=` to `run_next_task` signature
- running PR creation in dry_run or simulate mode
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- calling `gh` CLI directly in runner — must go through `CommandRunner`
- unused local variables that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_pr_creation_workflow.py` must cover:

- mergeable success path triggers PR creation
- review blocked does not trigger PR
- approval required does not trigger PR
- dry run does not trigger PR
- PR creation failure is handled gracefully

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

## CRITICAL — run_review signature must stay as single argument

`run_review` must keep its existing single-argument signature:

```python
def run_review(self, changed_files: list[str]) -> dict[str, Any]:
```

Do NOT add a second argument like `deliverables_updated`. Existing tests mock it as:
```python
runner.run_review = lambda changed_files: {"mergeable": False}
```
Adding a second parameter breaks these with `TypeError`.

`run_review` must use `PolicyEngine` internally:

```python
def run_review(self, changed_files: list[str]) -> dict[str, Any]:
    effective_changed = list(changed_files or [])

    if not effective_changed:
        return {"mergeable": True}

    approval_patterns = getattr(self.config, "approval_required_file_patterns", [])
    policy = PolicyEngine(
        approval_required_file_patterns=approval_patterns,
        protected_file_patterns=getattr(self.config, "protected_file_patterns", []),
    )
    if policy.requires_approval(effective_changed):
        return {"mergeable": False}

    checker = ReviewChecker(
        deliverables=effective_changed,
        changed_files=effective_changed,
    )
    result = checker.evaluate()
    if "mergeable" not in result:
        return {"mergeable": True}
    return result
```

## CRITICAL — deliverables_updated check in process_execution_result

When `deliverables_updated` is explicitly `[]` (empty list) AND `changed_files` is non-empty, block review BEFORE calling `run_review`:

```python
# On the success path, before calling run_review:
changed_files = execution_result.get("changed_files", [])
deliverables_updated = execution_result.get("deliverables_updated", [])

# Block if files changed but no deliverables updated
if changed_files and "deliverables_updated" in execution_result and len(deliverables_updated) == 0:
    log_review_verdict("blocked", None)
    checkpoint = create_approval_checkpoint(
        task_name=task.name,
        reason="no_deliverables_updated",
        source="review_gate",
        requested_action="requires_approval",
    )
    checkpoint["status"] = "pending_approval"
    log_approval_checkpoint(checkpoint, None)
    return {
        "task_name": task.name,
        "status": "running",
        "message": "Task is now running.",
        "outcome": "review_blocked",
        "next_action": "requires_approval",
        "requires_approval": True,
    }
```

Only block when `deliverables_updated` key is PRESENT and is an empty list.
When the key is ABSENT (legacy mock payloads), do NOT block.

## CRITICAL — final_status must be "completed" not "success"

`simulate_backlog` must initialize `final_status = "completed"` and never change it to `"success"`.

Valid values: `"completed"`, `"failed"`, `"blocked"`. Never `"success"`.

## CRITICAL — execute_task stdout/stderr must be stripped

Always call `.strip()` on subprocess output:
```python
"stdout": result.stdout.strip(),
"stderr": result.stderr.strip(),
```

Tests expect `"Task executed successfully"` not `"Task executed successfully\n"`.
