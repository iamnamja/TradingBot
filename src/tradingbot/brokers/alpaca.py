from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide
from tradingbot.brokers.base import Broker

class AlpacaBroker(Broker):
    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        self.client = TradingClient(api_key, api_secret, paper=paper)
        self.paper = paper

    def submit_order(self, symbol: str, qty: int, side: str) -> dict:
        if side not in ["buy", "sell"]:
            raise ValueError("Invalid side: must be 'buy' or 'sell'")
        if qty <= 0:
            raise ValueError("Quantity must be a positive integer")

        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force="day"
        )
        
        order = self.client.submit_order(order_request)
        return {
            "symbol": order.symbol,
            "qty": order.qty,
            "side": side,
            "status": order.status,
            "order_id": order.id if hasattr(order, 'id') else None
        }
