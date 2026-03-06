from dataclasses import dataclass
from typing import Literal

@dataclass
class OrderIntent:
    symbol: str
    qty: int
    side: Literal["buy", "sell"]
