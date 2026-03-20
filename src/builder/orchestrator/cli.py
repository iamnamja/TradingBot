from __future__ import annotations

import sys
from typing import Iterable

from .backlog import BacklogTracker
from .project_adapter import ProjectAdapter
from .runner import OrchestratorRunner
from .state import OrchestratorState


def _has_flag(argv: Iterable[str], flag: str) -> bool:
    return flag in argv


def _get_option_value(argv: list[str], option: str, default: int) -> int:
    if option not in argv:
        return default

    index = argv.index(option)
    if index + 1 >= len(argv):
        return default

    try:
        value = int(argv[index + 1])
    except ValueError:
        return default

    return value


def _print_run_loop_result(result: dict) -> None:
    processed_tasks = result.get("processed_tasks", [])
    for idx, task in enumerate(processed_tasks, start=1):
        task_name = task.get("task_name", "")
        outcome = task.get("outcome", "")
        next_action = task.get("next_action", "")
        print(f"[Task {idx}] {task_name} — {outcome} ({next_action})")

    print(f"Run complete: {result.get('final_status', '')}")
    print(f"Tasks processed: {result.get('count', len(processed_tasks))}")
    print(f"Stopped reason: {result.get('stopped_reason', '')}")


def main() -> int:
    config = ProjectAdapter.get_tradingbot_default_config()
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(
        config=config,
        backlog_tracker=backlog_tracker,
        initial_state=initial_state,
    )

    if _has_flag(sys.argv, "--skip-guardrails"):
        runner.skip_guardrails = True

    if _has_flag(sys.argv, "--simulate"):
        simulation_result = runner.simulate_backlog()
        print(
            "Processed Tasks: "
            f"{simulation_result['processed_tasks']}, "
            f"Stopped Reason: {simulation_result['stopped_reason']}, "
            f"Final Status: {simulation_result['final_status']}"
        )
        return 0

    if _has_flag(sys.argv, "run-loop"):
        max_tasks = _get_option_value(sys.argv, "--max-tasks", 100)
        result = runner.run_loop(max_tasks=max_tasks)
        _print_run_loop_result(result)
        return 0

    dry_run = _has_flag(sys.argv, "--dry-run")
    result = runner.run_next_task(dry_run=dry_run)

    print(
        "Task Name: "
        f"{result['task_name']}, "
        f"Status: {result['status']}, "
        f"Message: {result['message']}, "
        f"Outcome: {result.get('outcome', 'noop')}"
    )

    return 0 if result["status"] == "running" else 1


if __name__ == "__main__":
    sys.exit(main())
