from dataclasses import dataclass

@dataclass
class Bar:
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float
