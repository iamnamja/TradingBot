from time import time
from tradingbot.data.client import DataClient
from tradingbot.data.types import Bar
from typing import Dict, Tuple

class CachedDataClient(DataClient):
    def __init__(self, client: DataClient, ttl: int = 60):
        self.client = client
        self.ttl = ttl
        self.cache: Dict[Tuple[str, str, str, int], Tuple[float, float]] = {}

    def _cache_key(self, method: str, symbol: str, timeframe: str, limit: int) -> Tuple[str, str, str, int]:
        return (method, symbol, timeframe, limit)

    def get_latest_price(self, symbol: str) -> float:
        key = self._cache_key('get_latest_price', symbol, '', 0)
        cached = self.cache.get(key)
        if cached and time() - cached[1] < self.ttl:
            return cached[0]
        price = self.client.get_latest_price(symbol)
        self.cache[key] = (price, time())
        return price

    def get_bars(self, symbol: str, timeframe: str, limit: int) -> list[Bar]:
        key = self._cache_key('get_bars', symbol, timeframe, limit)
        cached = self.cache.get(key)
        if cached and time() - cached[1] < self.ttl:
            return cached[0]
        bars = self.client.get_bars(symbol, timeframe, limit)
        self.cache[key] = (bars, time())
        return bars
