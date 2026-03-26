"""Domain model: a real-time quote (last trade / NBBO)."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread(self) -> float:
        return self.ask - self.bid
