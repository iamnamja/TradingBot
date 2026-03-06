from typing import Protocol

class Broker(Protocol):
    def submit_order(self, symbol: str, qty: int, side: str) -> dict: ...
