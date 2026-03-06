from tradingbot.strategy.strategy_v1 import StrategyV1
from tradingbot.config.settings import Settings

class FakeDataClient:
    def __init__(self, bars):
        self.bars = bars

    def get_bars(self, symbol):
        return self.bars.get(symbol, [])

def test_no_candidates_when_rules_fail():
    data = FakeDataClient({
        "AAPL": [{"close": 150}] * 10,  # Not enough history
        "MSFT": [{"close": 250}] * 20,  # SMA(20) will be 250
    })
    cfg = Settings(env=None, mode="paper", dry_run=True, symbols=["AAPL", "MSFT"])
    candidates = StrategyV1.generate(["AAPL", "MSFT"], data, cfg)
    assert len(candidates) == 0

def test_candidate_fields_filled_correctly():
    data = FakeDataClient({
        "AAPL": [{"close": 155}] * 19 + [{"close": 160}],  # Last close above SMA(20)
    })
    cfg = Settings(env=None, mode="paper", dry_run=True, symbols=["AAPL"])
    candidates = StrategyV1.generate(["AAPL"], data, cfg)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.symbol == "AAPL"
    assert candidate.score > 0
    assert "Last close" in candidate.reason
    assert "sma20" in candidate.snapshot

def test_buy_candidate_created_when_conditions_met():
    data = FakeDataClient({
        "AAPL": [{"close": 150}] * 19 + [{"close": 160}],  # Last close above SMA(20)
    })
    cfg = Settings(env=None, mode="paper", dry_run=True, symbols=["AAPL"])
    candidates = StrategyV1.generate(["AAPL"], data, cfg)
    assert len(candidates) == 1
    assert candidates[0].symbol == "AAPL"
