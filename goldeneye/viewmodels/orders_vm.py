"""ViewModel: order blotter and order placement."""

import asyncio

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from goldeneye.models.order import Order, OrderSide, OrderType, TimeInForce
from goldeneye.services.broker.base import BrokerBase


class OrdersViewModel(QObject):
    orders_updated = pyqtSignal(list)    # list[Order]
    order_placed = pyqtSignal(object)    # Order
    error_occurred = pyqtSignal(str)

    def __init__(self, broker: BrokerBase, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._broker = broker
        self.orders: list[Order] = []

    def refresh(self) -> None:
        asyncio.run(self._async_refresh())

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        qty: float,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> None:
        asyncio.run(
            self._async_place(symbol, side, order_type, qty, time_in_force, limit_price, stop_price)
        )

    async def _async_refresh(self) -> None:
        try:
            self.orders = await self._broker.get_orders()
            self.orders_updated.emit(self.orders)
        except Exception as exc:
            logger.error("Order refresh failed: {}", exc)
            self.error_occurred.emit(str(exc))

    async def _async_place(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        qty: float,
        time_in_force: TimeInForce,
        limit_price: float | None,
        stop_price: float | None,
    ) -> None:
        try:
            order = await self._broker.place_order(
                symbol, side, order_type, qty, time_in_force, limit_price, stop_price
            )
            self.orders.append(order)
            self.order_placed.emit(order)
        except Exception as exc:
            logger.error("Place order failed: {}", exc)
            self.error_occurred.emit(str(exc))
