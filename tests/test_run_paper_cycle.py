from unittest.mock import patch, MagicMock
from tradingbot.paper.run_paper_cycle import main

@patch("tradingbot.paper.run_paper_cycle.load_settings")
@patch("tradingbot.paper.run_paper_cycle.print_startup_summary")
@patch("tradingbot.paper.run_paper_cycle.AlpacaBroker")
@patch("tradingbot.paper.run_paper_cycle.PortfolioStateLoader")
@patch("tradingbot.paper.run_paper_cycle.IntentPlanner")
@patch("tradingbot.paper.run_paper_cycle.ExecutionEngine")
@patch("tradingbot.paper.run_paper_cycle.CycleRunner")
def test_main_success(mock_cycle_runner, mock_execution_engine, mock_intent_planner, mock_portfolio_loader, mock_broker, mock_print_startup_summary, mock_load_settings):
    mock_load_settings.return_value.effective_mode = "paper"
    mock_load_settings.return_value.symbols = ["AAPL"]
    mock_broker.return_value = MagicMock()
    mock_portfolio_loader.return_value.load.return_value = (MagicMock(), [])
    mock_intent_planner.build_intents.return_value = [MagicMock()]
    mock_cycle_runner.return_value.run_once.return_value = {
        "market_hours_result": "open",
        "approved_count": 1,
        "risk_passed_count": 1,
        "order_intents_created": 1,
        "execution_results": [],
        "audit_path": "mock/audit/path.json"
    }

    exit_code = main()

    assert exit_code == 0
    mock_print_startup_summary.assert_called_once()
    mock_cycle_runner.return_value.run_once.assert_called_once()

@patch("tradingbot.paper.run_paper_cycle.load_settings")
def test_main_live_mode(mock_load_settings):
    mock_load_settings.return_value.effective_mode = "live"

    exit_code = main()

    assert exit_code == 1
