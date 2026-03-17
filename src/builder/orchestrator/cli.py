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
    
    # Support --skip-guardrails flag for testing purposes only
    if "--skip-guardrails" in sys.argv:
        runner.skip_guardrails = True
    
    dry_run = "--dry-run" in sys.argv
    if "--simulate" in sys.argv:
        simulation_result = runner.simulate_backlog()
        print(f"Processed Tasks: {simulation_result['processed_tasks']}, Stopped Reason: {simulation_result['stopped_reason']}, Final Status: {simulation_result['final_status']}")
        return 0

    result = runner.run_next_task(dry_run=dry_run)
    
    print(f"Task Name: {result['task_name']}, Status: {result['status']}, Message: {result['message']}, Outcome: {result.get('outcome', 'noop')}")
    
    return 0 if result['status'] == "running" else 1

if __name__ == "__main__":
    sys.exit(main())
