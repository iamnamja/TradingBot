from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
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


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _append_decision_log_entry(audit_path: str | None, entry: dict) -> None:
    if not audit_path:
        return

    try:
        path = Path(audit_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        return


def _log_run_loop_decisions(result: dict, audit_path: str | None) -> None:
    if not audit_path:
        return

    processed_tasks = result.get("processed_tasks", [])
    for iteration, task in enumerate(processed_tasks, start=1):
        task_name = task.get("task_name", "")
        status = task.get("status", "")
        if task_name == "none" or status == "no_task":
            continue

        _append_decision_log_entry(
            audit_path,
            {
                "task_name": str(task_name),
                "outcome": str(task.get("outcome", "")),
                "timestamp": _timestamp(),
                "iteration": iteration,
            },
        )


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
        print(f"Simulation complete: {simulation_result}")
        return 0

    if _has_flag(sys.argv, "run-loop"):
        max_tasks = _get_option_value(sys.argv, "--max-tasks", 100)
        result = runner.run_loop(max_tasks=max_tasks)
        _print_run_loop_result(result)
        _log_run_loop_decisions(result, getattr(config, "audit_path", None))
        return 0

    result = runner.run_next_task()
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
