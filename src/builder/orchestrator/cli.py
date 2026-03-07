import sys
from .runner import OrchestratorRunner
from .backlog import BacklogTracker
from .state import OrchestratorState
from .project_adapter import ProjectAdapter

def main() -> int:
    # Initialize components
    config = ProjectAdapter.get_tradingbot_default_config()
    backlog_tracker = BacklogTracker(tasks_directory=config.tasks_directory)
    initial_state = OrchestratorState(tasks=[])

    runner = OrchestratorRunner(config=config, backlog_tracker=backlog_tracker, initial_state=initial_state)
    
    # Run the orchestrator for one cycle
    result = runner.run_next_task()
    
    print(f"Task Name: {result['task_name']}, Status: {result['status']}, Message: {result['message']}")
    
    return 0 if result['status'] == "running" else 1

if __name__ == "__main__":
    sys.exit(main())
