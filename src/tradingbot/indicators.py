from typing import List, Optional

def sma(values: List[float], window: int) -> List[Optional[float]]:
    if window <= 0:
        return [None] * len(values)

    result = [None] * len(values)
    for i in range(len(values)):
        if i < window - 1:
            result[i] = None
        else:
            result[i] = sum(values[i - window + 1:i + 1]) / window
    return result

def rsi(values: List[float], window: int = 14) -> List[Optional[float]]:
    if window <= 0:
        return [None] * len(values)

    if len(values) <= 1:
        return [None] * len(values)

    if window > len(values) - 1:
        return [None] * len(values)

    result = [None] * len(values)

    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        if delta > 0:
            result[i] = 100.0
        else:
            result[i] = 0.0

    return result

def trend_up(values: List[float], lookback: int = 5) -> bool:
    if len(values) < lookback:
        return False
    return values[-1] > values[-lookback]
