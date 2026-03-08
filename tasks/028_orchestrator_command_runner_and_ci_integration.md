# Task 028: Orchestrator command runner and CI integration

## Goal
Replace purely simulated command behavior with a reusable command-runner abstraction that can drive PR/CI/merge operations safely and testably.

## Deliverables
- updates to:
  - `src/builder/orchestrator/merge.py`
- new file:
  - `src/builder/orchestrator/command_runner.py`
- `tests/test_orchestrator_command_runner.py`
- `tests/test_merge_manager_integration.py`

## Existing repo dependencies (NOT deliverables)
Reuse the current merge manager shape rather than replacing the whole orchestrator interface.

## Scope
This task is about command abstraction and CI/merge integration, not full autonomous looping.

## Required behavior

### Command-runner abstraction
Introduce a reusable command-runner layer that:
- can execute commands
- can be stubbed or mocked in tests
- returns structured results

Required structured result fields:
- `returncode: int`
- `stdout: str`
- `stderr: str`

Optional:
- `timed_out: bool`

### Merge-manager integration
`MergeManager` should use the command runner rather than hardcoded or fake inline behavior.

Required supported operations:
- create PR
- check or poll CI status
- enable merge / merge PR
- sync local main

### CI state contract
This is the most important rule in the task.

The merge manager must distinguish at least:
- pending
- passed
- failed

It must not collapse pending and failed into the same result.

### Safety
The merge manager must not merge if:
- CI failed
- CI is still pending
- review/policy says approval is required
- review checker says not mergeable

### Output contract
Merge-manager methods must return deterministic primitive-valued results, not raw command-runner objects.

Example fields:
- `status`
- `can_merge`
- `reason`
- `pr_url`

### Command construction contract
Tests should be able to verify which command would be run, without requiring a real git/GitHub environment.
Do not hardcode repo names or branch names into the merge manager.

### Test guidance
Tests must not require live GitHub or git access.
Use mocked command-runner responses.

Tests must cover at least:
- create PR success
- CI pending
- CI failed
- CI passed + merge allowed
- merge blocked by approval requirement
- sync-main command invocation

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- command execution is abstracted behind a reusable runner
- merge decisions respect CI state distinctions and safety checks
- merge-manager outputs are deterministic and primitive-valued
