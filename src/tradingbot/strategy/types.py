from dataclasses import dataclass

@dataclass
class Candidate:
    symbol: str
    score: float
    reason: str
    snapshot: dict
