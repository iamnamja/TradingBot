from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tradingbot.config.settings import Settings
from tradingbot.cycle.runner import CycleRunner
from tradingbot.data.client import DataClient
from tradingbot.execution.engine import ExecutionEngine
from tradingbot.llm.advisor import LLMAdvisor
from tradingbot.risk.risk_gate import RiskGate


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


def test_cycle_runner_uses_temp_audit_path(
    tmp_path,
    mock_data_client,
    mock_llm_advisor,
    mock_risk_gate,
    mock_execution_engine,
    settings,
):
    runner = CycleRunner(
        mock_data_client,
        mock_llm_advisor,
        mock_risk_gate,
        mock_execution_engine,
        settings,
    )

    mock_data_client.get_latest_price.return_value = 150.0
    mock_data_client.get_bars.return_value = [{"close": 150.0}] * 20
    mock_llm_advisor.review.return_value = [
        MagicMock(symbol="AAPL", action="approve", reason="good candidate")
    ]
    mock_risk_gate.evaluate.return_value = (True, "trade allowed")

    audit_file = tmp_path / "audit.json"

    def fake_write_audit(event: dict, path: str = "logs/") -> str:
        audit_file.write_text("{}", encoding="utf-8")
        return str(audit_file)

    with patch("tradingbot.cycle.runner.write_audit", side_effect=fake_write_audit):
        result = runner.run_once()

    assert "audit_path" in result
    assert Path(result["audit_path"]).exists()
    assert Path(result["audit_path"]).parent == tmp_path
