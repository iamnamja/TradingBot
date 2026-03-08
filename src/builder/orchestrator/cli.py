import sys
from .runner import OrchestratorRunner
from .backlog import BacklogTracker
from .state import OrchestratorState
from .project_adapter import ProjectAdapter

def main() -> int:
    config = ProjectAdapter.get_tradingbot_default_config()
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(config=config, backlog_tracker=backlog_tracker, initial_state=initial_state)
    
    dry_run = "--dry-run" in sys.argv
    result = runner.run_next_task(dry_run=dry_run)
    
    print(f"Task Name: {result['task_name']}, Status: {result['status']}, Message: {result['message']}, Outcome: {result.get('outcome', 'noop')}")
    
    return 0 if result['status'] == "running" else 1

if __name__ == "__main__":
    sys.exit(main())
