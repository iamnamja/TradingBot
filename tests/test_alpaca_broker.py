from unittest.mock import patch, MagicMock
import pytest
from tradingbot.brokers.alpaca import AlpacaBroker

@patch("tradingbot.brokers.alpaca.TradingClient")
def test_submit_order_valid(mock_trading_client):
    mock_client_instance = MagicMock()
    mock_trading_client.return_value = mock_client_instance
    mock_order = MagicMock()
    mock_order.symbol = "AAPL"
    mock_order.qty = 10
    mock_order.status = "submitted"
    mock_order.id = "order_id_123"
    mock_client_instance.submit_order.return_value = mock_order

    broker = AlpacaBroker("api_key", "api_secret", paper=True)
    result = broker.submit_order("AAPL", 10, "buy")

    assert result == {
        "symbol": "AAPL",
        "qty": 10,
        "side": "buy",
        "status": "submitted",
        "order_id": "order_id_123"
    }

@patch("tradingbot.brokers.alpaca.TradingClient")
def test_submit_order_invalid_side(mock_trading_client):
    broker = AlpacaBroker("api_key", "api_secret", paper=True)
    with pytest.raises(ValueError, match="Invalid side: must be 'buy' or 'sell'"):
        broker.submit_order("AAPL", 10, "invalid_side")

@patch("tradingbot.brokers.alpaca.TradingClient")
def test_submit_order_invalid_qty(mock_trading_client):
    broker = AlpacaBroker("api_key", "api_secret", paper=True)
    with pytest.raises(ValueError, match="Quantity must be a positive integer"):
        broker.submit_order("AAPL", 0, "buy")

@patch("tradingbot.brokers.alpaca.TradingClient")
def test_paper_mode_passed_to_client(mock_trading_client):
    broker = AlpacaBroker("api_key", "api_secret", paper=True)
    mock_trading_client.assert_called_once_with("api_key", "api_secret", paper=True)
    assert broker.paper is True
