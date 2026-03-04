from dataclasses import dataclass
from typing import Dict

@dataclass
class PortfolioState:
    cash_usd: float
    open_positions: Dict[str, float]
    trades_today: int
