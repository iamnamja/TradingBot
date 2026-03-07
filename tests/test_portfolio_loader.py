from unittest.mock import MagicMock
import pytest
from tradingbot.portfolio.loader import PortfolioStateLoader
from tradingbot.portfolio.types import AccountState, PositionState

@pytest.fixture
def mock_broker():
    broker = MagicMock()
    broker.get_account.return_value = MagicMock(cash=10000, equity=15000, buying_power=12000)
    broker.get_all_positions.return_value = [
        MagicMock(symbol="AAPL", qty=10, market_value=1500),
        MagicMock(symbol="MSFT", qty=5, market_value=750),
    ]
    return broker

def test_load_account_state(mock_broker):
    loader = PortfolioStateLoader(mock_broker)
    account_state, positions = loader.load()

    assert isinstance(account_state, AccountState)
    assert account_state.cash_usd == 10000
    assert account_state.equity_usd == 15000
    assert account_state.buying_power_usd == 12000

    assert len(positions) == 2
    assert positions[0] == PositionState(symbol="AAPL", qty=10, market_value_usd=1500)
    assert positions[1] == PositionState(symbol="MSFT", qty=5, market_value_usd=750)

def test_load_empty_positions(mock_broker):
    mock_broker.get_all_positions.return_value = []
    loader = PortfolioStateLoader(mock_broker)
    account_state, positions = loader.load()

    assert isinstance(account_state, AccountState)
    assert account_state.cash_usd == 10000
    assert account_state.equity_usd == 15000
    assert account_state.buying_power_usd == 12000

    assert positions == []
