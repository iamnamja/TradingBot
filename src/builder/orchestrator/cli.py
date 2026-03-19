from __future__ import annotations

import sys
from typing import List, Tuple

from .backlog import BacklogTracker
from .project_adapter import ProjectAdapter
from .runner import OrchestratorRunner
from .state import OrchestratorState


def _parse_flag_with_value(argv: List[str], flag: str) -> Tuple[bool, str | None]:
    if flag in argv:
        try:
            idx = argv.index(flag)
            # Guard against missing value
            if idx + 1 < len(argv) and not argv[idx + 1].startswith("-"):
                return True, argv[idx + 1]
            return True, None
        except Exception:
            return True, None
    return False, None


def main() -> int:
    argv = list(sys.argv)
    # Instantiate runner with default tradingbot adapter for now
    config = ProjectAdapter.get_tradingbot_default_config()
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(config=config, backlog_tracker=backlog_tracker, initial_state=initial_state)

    # Global flags
    if "--skip-guardrails" in argv:
        runner.skip_guardrails = True

    dry_run = "--dry-run" in argv

    # Optional audit path flag (not part of ProjectConfig dataclass; set dynamically)
    has_audit_flag, audit_path = _parse_flag_with_value(argv, "--audit-path")
    if has_audit_flag and audit_path:
        setattr(runner.config, "audit_path", audit_path)

    # Optional max-tasks flag for run-loop
    has_max_flag, max_tasks_val = _parse_flag_with_value(argv, "--max-tasks")
    max_tasks = 100
    if has_max_flag:
        try:
            max_tasks = int(max_tasks_val or "100")
        except Exception:
            max_tasks = 100

    # Subcommands/modes
    if "simulate" in argv or "--simulate" in argv:
        simulation_result = runner.simulate_backlog()
        print(
            f"Processed Tasks: {simulation_result['processed_tasks']}, "
            f"Stopped Reason: {simulation_result['stopped_reason']}, "
            f"Final Status: {simulation_result['final_status']}"
        )
        return 0

    if "run-loop" in argv or "--run-loop" in argv:
        summary = runner.run_loop(max_tasks=max_tasks)
        # Final summary
        print(f"Run complete: {summary['final_status']}")
        print(f"Tasks processed: {len(summary['processed_tasks'])}")
        print(f"Stopped reason: {summary['stopped_reason']}")
        return 0 if summary["final_status"] == "completed" else 1

    if "resume" in argv or "--resume" in argv:
        # Placeholder: in a fuller implementation this would inspect checkpoints/state
        result = runner.run_next_task(dry_run=False)
        # Print a one-line summary for visibility
        task_name = result.get("task_name", "none")
        outcome = result.get("outcome", "noop")
        next_action = result.get("next_action", "none")
        print(f"[Task] {task_name} — {outcome} ({next_action})")
        return 0

    # Default / run-once mode
    if "run-once" in argv or "--run-once" in argv or True:
        result = runner.run_next_task(dry_run=dry_run)
        task_name = result.get("task_name", "none")
        outcome = result.get("outcome", "noop")
        next_action = result.get("next_action", "none")
        status = result.get("status", "")
        message = result.get("message", "")
        # Print a concise one-line followed by status line for manual use
        print(f"[Task] {task_name} — {outcome} ({next_action})")
        if message:
            print(f"{status}: {message}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
