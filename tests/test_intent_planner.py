import pytest
from tradingbot.execution.types import OrderIntent
from tradingbot.planner.intent_planner import IntentPlanner

class MockCandidate:
    def __init__(self, symbol, last_close):
        self.symbol = symbol
        self.snapshot = {"last_close": last_close}

class MockAccountState:
    def __init__(self):
        self.cash_usd = 10000
        self.equity_usd = 15000
        self.buying_power_usd = 12000

class MockPositionState:
    def __init__(self, symbol, qty):
        self.symbol = symbol
        self.qty = qty

@pytest.fixture
def cfg():
    class MockSettings:
        max_position_size_usd = 1000
    return MockSettings()

def test_valid_candidate_produces_order_intent(cfg):
    candidates = [MockCandidate("AAPL", 100)]
    account = MockAccountState()
    positions = []
    intents = IntentPlanner.build_intents(candidates, account, positions, cfg)
    assert len(intents) == 1
    assert intents[0] == OrderIntent(symbol="AAPL", qty=10, side="buy")

def test_qty_floors_correctly(cfg):
    candidates = [MockCandidate("AAPL", 150)]
    account = MockAccountState()
    positions = []
    intents = IntentPlanner.build_intents(candidates, account, positions, cfg)
    assert len(intents) == 1
    assert intents[0] == OrderIntent(symbol="AAPL", qty=6, side="buy")

def test_candidate_with_missing_last_close_is_skipped(cfg):
    candidates = [MockCandidate("AAPL", None)]
    account = MockAccountState()
    positions = []
    intents = IntentPlanner.build_intents(candidates, account, positions, cfg)
    assert len(intents) == 0

def test_candidate_with_too_high_price_is_skipped(cfg):
    candidates = [MockCandidate("AAPL", 2000)]
    account = MockAccountState()
    positions = []
    intents = IntentPlanner.build_intents(candidates, account, positions, cfg)
    assert len(intents) == 0

def test_planner_is_deterministic(cfg):
    candidates = [MockCandidate("AAPL", 100), MockCandidate("MSFT", 150)]
    account = MockAccountState()
    positions = []
    intents = IntentPlanner.build_intents(candidates, account, positions, cfg)
    assert len(intents) == 2
    assert intents[0] == OrderIntent(symbol="AAPL", qty=10, side="buy")
    assert intents[1] == OrderIntent(symbol="MSFT", qty=6, side="buy")
