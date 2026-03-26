"""Abstract broker interface – swap Alpaca for any other provider."""

from abc import ABC, abstractmethod

from goldeneye.models.order import Order, OrderSide, OrderType, TimeInForce
from goldeneye.models.portfolio import Portfolio
from goldeneye.models.position import Position


class BrokerBase(ABC):
    """All broker adapters must implement this interface."""

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def get_portfolio(self) -> Portfolio: ...

    @abstractmethod
    async def get_positions(self) -> list[Position]: ...

    @abstractmethod
    async def get_orders(self) -> list[Order]: ...

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        qty: float,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> Order: ...

    @abstractmethod
    async def cancel_order(self, broker_id: str) -> None: ...
