import sys
from tradingbot.config.settings import load_settings, print_startup_summary
from tradingbot.brokers.alpaca import AlpacaBroker
from tradingbot.portfolio.loader import PortfolioStateLoader
from tradingbot.planner.intent_planner import IntentPlanner
from tradingbot.execution.engine import ExecutionEngine
from tradingbot.cycle.runner import CycleRunner

def main() -> int:
    settings = load_settings()
    
    if settings.effective_mode == "live":
        print("Error: This command can only be run in paper mode.")
        return 1

    print_startup_summary(settings)

    broker = AlpacaBroker(settings.env.alpaca_api_key, settings.env.alpaca_api_secret, paper=True)
    loader = PortfolioStateLoader(broker)
    account_state, positions = loader.load()

    candidates = IntentPlanner.build_intents(settings.symbols, account_state, positions, settings)
    
    execution_engine = ExecutionEngine()
    cycle_runner = CycleRunner(broker, execution_engine, settings)

    result = cycle_runner.run_once()

    print("Cycle Summary:")
    print(f"  Market Hours Result: {result.get('market_hours_result')}")
    print(f"  Candidate Count: {len(candidates)}")
    print(f"  Approved Count: {result.get('approved_count')}")
    print(f"  Risk Passed Count: {result.get('risk_passed_count')}")
    print(f"  Order Intents Created: {result.get('order_intents_created')}")
    print(f"  Execution Results: {result.get('execution_results')}")
    print(f"  Audit File Path: {result.get('audit_path')}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
