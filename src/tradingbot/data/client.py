from typing import Protocol, List
from tradingbot.data.types import Bar

class DataClient(Protocol):
    def get_latest_price(self, symbol: str) -> float:
        ...

    def get_bars(self, symbol: str, timeframe: str, limit: int) -> List[Bar]:
        ...
