import pytest
from tradingbot.risk.types import PortfolioState
from tradingbot.risk.risk_gate import RiskGate

class MockCandidate:
    def __init__(self, size):
        self.size = size

class MockSettings:
    def __init__(self, max_position_size_usd, max_open_positions, max_trades_per_day):
        self.max_position_size_usd = max_position_size_usd
        self.max_open_positions = max_open_positions
        self.max_trades_per_day = max_trades_per_day

@pytest.fixture
def risk_gate():
    return RiskGate()

def test_deny_when_max_positions_reached(risk_gate):
    state = PortfolioState(cash_usd=10000, open_positions={'AAPL': 100}, trades_today=0)
    candidate = MockCandidate(size=100)
    cfg = MockSettings(max_position_size_usd=5000, max_open_positions=1, max_trades_per_day=5)
    
    result = risk_gate.evaluate(candidate, state, cfg)
    assert result == (False, "risk denied: max positions reached")

def test_deny_when_trade_size_exceeds_max(risk_gate):
    state = PortfolioState(cash_usd=10000, open_positions={}, trades_today=0)
    candidate = MockCandidate(size=6000)
    cfg = MockSettings(max_position_size_usd=5000, max_open_positions=5, max_trades_per_day=5)
    
    result = risk_gate.evaluate(candidate, state, cfg)
    assert result == (False, "risk denied: trade size exceeds max")

def test_allow_when_within_limits(risk_gate):
    state = PortfolioState(cash_usd=10000, open_positions={}, trades_today=0)
    candidate = MockCandidate(size=4000)
    cfg = MockSettings(max_position_size_usd=5000, max_open_positions=5, max_trades_per_day=5)
    
    result = risk_gate.evaluate(candidate, state, cfg)
    assert result == (True, "trade allowed")
