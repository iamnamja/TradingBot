from tradingbot.indicators import sma, rsi, trend_up

def test_sma():
    assert sma([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]
    assert sma([1, 2, 3, 4, 5], 3) == [None, None, 2.0, 3.0, 4.0]
    assert sma([], 2) == []
    assert sma([1], 2) == [None]

def test_rsi():
    assert rsi([1, 2, 3, 4, 5], 14) == [None, None, None, None, None]
    assert rsi([1, 2, 1, 2, 1], 2) == [None, 100.0, 0.0, 100.0, 0.0]
    assert rsi([1, 1, 1, 1], 2) == [None, 0.0, 0.0, 0.0]
    assert rsi([], 2) == []
    assert rsi([1], 2) == [None]

def test_trend_up():
    assert trend_up([1, 2, 3, 4, 5], 5) is True
    assert trend_up([5, 4, 3, 2, 1], 5) is False
    assert trend_up([1, 2], 5) is False
    assert trend_up([], 5) is False
