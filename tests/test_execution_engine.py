from tradingbot.execution.engine import ExecutionEngine
from tradingbot.execution.types import OrderIntent

class FakeBroker:
    def __init__(self):
        self.orders = []

    def submit_order(self, symbol: str, qty: int, side: str) -> dict:
        order = {"symbol": symbol, "qty": qty, "side": side, "status": "submitted"}
        self.orders.append(order)
        return order

def test_execute_dry_run():
    engine = ExecutionEngine()
    broker = FakeBroker()
    cfg = type('Settings', (object,), {'effective_dry_run': True})()

    intents = [OrderIntent(symbol="AAPL", qty=10, side="buy")]
    results = engine.execute(intents, broker, cfg)

    assert len(results) == 1
    assert results[0]["status"] == "dry_run"

def test_execute_real_order():
    engine = ExecutionEngine()
    broker = FakeBroker()
    cfg = type('Settings', (object,), {'effective_dry_run': False})()

    intents = [OrderIntent(symbol="AAPL", qty=10, side="buy")]
    results = engine.execute(intents, broker, cfg)

    assert len(results) == 1
    assert results[0]["status"] == "submitted"
    assert broker.orders[0] == results[0]
