"""Domain model: a brokerage order."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TimeInForce(StrEnum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


@dataclass
class Order:
    symbol: str
    side: OrderSide
    order_type: OrderType
    qty: float
    time_in_force: TimeInForce = TimeInForce.DAY
    limit_price: float | None = None
    stop_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    broker_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: datetime | None = None
    filled_avg_price: float | None = None
    filled_qty: float = 0.0
