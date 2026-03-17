# Task 034 — Branch and Worktree Guardrails

## Goal

Prevent orchestrator real execution in unsafe git states. Simulation mode must bypass all guardrails.

## Why

Real execution should never run on `main`, with a dirty worktree, or on a branch that doesn't match the expected task branch pattern. These guardrails prevent accidental commits to protected branches.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged
- Simulation mode must bypass all guardrails — existing simulation tests must not be broken

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/git_guardrails.py`
- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_git_guardrails.py`

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

### git_guardrails.py

Must define a `GitGuardrails` class:

```python
class GitGuardrails:
    def __init__(self, branch_naming_pattern: str) -> None: ...
    def check(self) -> tuple[bool, str]:
        """Returns (safe: bool, reason: str)"""
```

`check()` must fail (return `False`) when:
- current branch is `main`
- worktree has uncommitted changes (`git status --porcelain` is non-empty)
- current branch name does not match `branch_naming_pattern`

`check()` must pass (return `True`) when:
- on a valid non-main branch matching the pattern
- worktree is clean

### runner.py integration

`run_next_task()` must call `GitGuardrails.check()` before executing a task.

If the check fails, `run_next_task()` must return:
```python
{
    "task_name": "none",
    "status": "blocked",
    "message": f"Git guardrail failed: {reason}",
    "outcome": "guardrail_failed",
    "next_action": "fix_git_state",
    "requires_approval": False,
}
```

Guardrails must only run when NOT in dry_run mode and NOT in simulate mode.

`simulate_backlog()` must NOT call guardrails — simulation must always be safe to run.

### cli.py

Must support a `--skip-guardrails` flag for testing purposes only.

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

When no pending task:
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`

When execution fails:
- `status == "failed"`
- `outcome == "repair_required"`

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

- calling guardrails inside `simulate_backlog`
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- unused local variables that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_git_guardrails.py` must cover:

- running on `main` branch is blocked
- dirty worktree is blocked
- valid branch passes
- simulation mode bypasses all guardrails

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

## CRITICAL — guardrails must not run when task_runner_command is None

Existing tests do not set up a real git environment. Guardrails must ONLY run when `task_runner_command` is configured (real execution mode).

```python
def run_next_task(self, dry_run: bool = False) -> Dict[str, Union[str, bool]]:
    self.read_backlog()
    next_task = self.select_next_task()

    if not next_task:
        return { ... no_task response ... }

    if dry_run:
        return { ... dry_run response ... }

    # Only run guardrails in real execution mode
    task_runner_command = getattr(self.config, "task_runner_command", None)
    skip_guardrails = getattr(self, "skip_guardrails", False)

    if task_runner_command and not skip_guardrails:
        guardrails = GitGuardrails(
            branch_naming_pattern=self.config.branch_naming_pattern
        )
        safe, reason = guardrails.check()
        if not safe:
            return {
                "task_name": "none",
                "status": "blocked",
                "message": f"Git guardrail failed: {reason}",
                "outcome": "guardrail_failed",
                "next_action": "fix_git_state",
                "requires_approval": False,
            }

    # ... rest of execution
```

This means:
- Tests without `task_runner_command` → guardrails never run → existing tests pass
- Tests with `task_runner_command` and mocked `subprocess.run` → guardrails run on mocked git
- `runner.skip_guardrails = True` → guardrails skipped even with real command

## CRITICAL — execute_task real path must return full structured dict

When `task_runner_command` is configured, `execute_task` must return ALL of:

```python
{
    "success": result.returncode == 0,
    "status": "success" if result.returncode == 0 else "failure",
    "stdout": result.stdout.strip(),
    "stderr": result.stderr.strip(),
    "returncode": result.returncode,
    "task_file": str(task_file_path),
    "changed_files": [],
}
```

Note: `changed_files` must be included even on the real path — default to `[]`.

## CRITICAL — execute_task mock path must return changed_files: []

When `task_runner_command` is None:

```python
return {
    "success": True,
    "output": "Task executed successfully",
    "changed_files": [],
}
```

The `test_execute_task_without_real_command` test expects `result["changed_files"] == []`.

Do NOT return `"changed_files": ["file1.py"]` on the mock path.

The legacy `ready_for_pr` path still works because `run_review([])` returns `{"mergeable": True}`.

## CRITICAL — simulate_backlog must use BacklogTracker.scan_tasks for real dirs

`test_simulate_bypasses_guardrails` creates a real temp directory with one task file and expects `len(processed_tasks) == 1`. This means `simulate_backlog` must be able to discover tasks from the real filesystem when `BacklogTracker` is backed by a real directory.

The `simulate_backlog` loop calls `get_next_task([])` which works with mocked trackers. For real `BacklogTracker` instances, `get_next_task([])` with an empty list will return `None` because there are no tasks in the list.

To support both mocked and real backlog trackers, `simulate_backlog` must call `select_next_task()` which goes through `scan_tasks()` properly:

```python
# In simulate_backlog, use select_next_task() which calls scan_tasks internally
while True:
    next_task = self.select_next_task()
    if not next_task:
        break
    ...
```

BUT this breaks the `side_effect` mock pattern. The solution: detect which path to use based on whether `get_next_task` has a `side_effect` set:

Actually the correct fix is simpler: the test sets up a real `BacklogTracker` with a real dir. Call `self.backlog_tracker.get_next_task(self.backlog_tracker.scan_tasks())` inside simulate_backlog:

```python
while True:
    tasks = self.backlog_tracker.scan_tasks()
    next_task = self.backlog_tracker.get_next_task(tasks)
    if not next_task:
        break
    ...
```

This works for BOTH cases:
- Mock with `side_effect`: `scan_tasks()` returns whatever it's mocked to, `get_next_task` uses `side_effect`
- Real `BacklogTracker`: `scan_tasks()` scans the real dir, `get_next_task` picks the first pending

Update the `simulate_backlog` loop to use `scan_tasks()` before `get_next_task` on each iteration.
