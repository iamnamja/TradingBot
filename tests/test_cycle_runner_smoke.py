import os
import pytest
from unittest.mock import MagicMock
from tradingbot.cycle.runner import CycleRunner
from tradingbot.data.client import DataClient
from tradingbot.llm.advisor import LLMAdvisor
from tradingbot.risk.risk_gate import RiskGate
from tradingbot.execution.engine import ExecutionEngine
from tradingbot.config.settings import Settings

@pytest.fixture
def mock_data_client():
    return MagicMock(spec=DataClient)

@pytest.fixture
def mock_llm_advisor():
    return MagicMock(spec=LLMAdvisor)

@pytest.fixture
def mock_risk_gate():
    return MagicMock(spec=RiskGate)

@pytest.fixture
def mock_execution_engine():
    return MagicMock(spec=ExecutionEngine)

@pytest.fixture
def settings():
    return Settings(env=None, mode="paper", dry_run=True, symbols=["AAPL", "MSFT"])

def test_cycle_runner(mock_data_client, mock_llm_advisor, mock_risk_gate, mock_execution_engine, settings):
    runner = CycleRunner(mock_data_client, mock_llm_advisor, mock_risk_gate, mock_execution_engine, settings)
    
    # Mocking the behavior of the data client and LLM advisor
    mock_data_client.get_latest_price.return_value = 150.0
    mock_data_client.get_bars.return_value = [{"close": 150}] * 20
    mock_llm_advisor.review.return_value = [MagicMock(symbol="AAPL", action="approve", reason="good candidate")]

    # Mocking risk gate evaluation
    mock_risk_gate.evaluate.return_value = (True, "trade allowed")

    result = runner.run_once()

    assert "audit_path" in result
    assert os.path.exists(result["audit_path"])
    assert os.path.dirname(result["audit_path"]) == "logs"
