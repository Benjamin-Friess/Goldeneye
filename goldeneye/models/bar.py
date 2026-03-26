"""Domain model: an OHLCV price bar."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float = 0.0
