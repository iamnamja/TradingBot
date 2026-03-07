from unittest.mock import patch, MagicMock
import pytest
from tradingbot.brokers.alpaca import AlpacaBroker

@pytest.fixture
def mock_trading_client():
    with patch("tradingbot.brokers.alpaca.TradingClient") as mock:
        yield mock

def test_alpaca_broker_initialization(mock_trading_client):
    broker = AlpacaBroker("test_api_key", "test_api_secret", paper=True)
    mock_trading_client.assert_called_once_with("test_api_key", "test_api_secret", paper=True)
    assert broker.paper is True

def test_submit_order_valid(mock_trading_client):
    broker = AlpacaBroker("test_api_key", "test_api_secret", paper=True)
    mock_order = MagicMock()
    mock_order.symbol = "AAPL"
    mock_order.qty = 10
    mock_order.status = "submitted"
    mock_order.id = "order_id_123"
    mock_trading_client.return_value.submit_order.return_value = mock_order

    result = broker.submit_order("AAPL", 10, "buy")
    assert result == {
        "symbol": "AAPL",
        "qty": 10,
        "side": "buy",
        "status": "submitted",
        "order_id": "order_id_123"
    }

def test_submit_order_invalid_side(mock_trading_client):
    broker = AlpacaBroker("test_api_key", "test_api_secret", paper=True)
    with pytest.raises(ValueError, match="Invalid side: must be 'buy' or 'sell'"):
        broker.submit_order("AAPL", 10, "invalid_side")

def test_submit_order_invalid_qty(mock_trading_client):
    broker = AlpacaBroker("test_api_key", "test_api_secret", paper=True)
    with pytest.raises(ValueError, match="Quantity must be positive"):
        broker.submit_order("AAPL", 0, "buy")

def test_submit_order_negative_qty(mock_trading_client):
    broker = AlpacaBroker("test_api_key", "test_api_secret", paper=True)
    with pytest.raises(ValueError, match="Quantity must be positive"):
        broker.submit_order("AAPL", -5, "sell")
