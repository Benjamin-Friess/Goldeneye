"""Alpaca broker adapter."""

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    OrderSide as AlpacaSide,
    OrderType as AlpacaType,
    TimeInForce as AlpacaTIF,
)
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from loguru import logger

from goldeneye.core.config import settings
from goldeneye.core.exceptions import BrokerError
from goldeneye.models.order import Order, OrderSide, OrderStatus, OrderType, TimeInForce
from goldeneye.models.portfolio import Portfolio
from goldeneye.models.position import Position
from goldeneye.services.broker.base import BrokerBase


class AlpacaBroker(BrokerBase):
    def __init__(self) -> None:
        self._client: TradingClient | None = None

    async def connect(self) -> None:
        logger.info("Connecting to Alpaca (paper={})", settings.alpaca_paper)
        self._client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=settings.alpaca_paper,
        )

    async def disconnect(self) -> None:
        self._client = None

    def _require_client(self) -> TradingClient:
        if self._client is None:
            raise BrokerError("Not connected. Call connect() first.")
        return self._client

    async def get_portfolio(self) -> Portfolio:
        client = self._require_client()
        account = client.get_account()
        positions = await self.get_positions()
        return Portfolio(
            cash=float(account.cash),
            positions={p.symbol: p for p in positions},
        )

    async def get_positions(self) -> list[Position]:
        client = self._require_client()
        raw = client.get_all_positions()
        return [
            Position(
                symbol=p.symbol,
                qty=float(p.qty),
                avg_entry_price=float(p.avg_entry_price),
                current_price=float(p.current_price or 0),
            )
            for p in raw
        ]

    async def get_orders(self) -> list[Order]:
        client = self._require_client()
        raw = client.get_orders()
        return [
            Order(
                symbol=o.symbol,
                side=OrderSide(o.side.value),
                order_type=OrderType(o.order_type.value),
                qty=float(o.qty or 0),
                status=OrderStatus(o.status.value),
                broker_id=str(o.id),
            )
            for o in raw
        ]

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        qty: float,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> Order:
        client = self._require_client()
        alpaca_side = AlpacaSide(side.value)
        alpaca_tif = AlpacaTIF(time_in_force.value)

        if order_type == OrderType.MARKET:
            req = MarketOrderRequest(symbol=symbol, qty=qty, side=alpaca_side, time_in_force=alpaca_tif)
        elif order_type == OrderType.LIMIT and limit_price is not None:
            req = LimitOrderRequest(symbol=symbol, qty=qty, side=alpaca_side, time_in_force=alpaca_tif, limit_price=limit_price)  # type: ignore[assignment]
        elif order_type == OrderType.STOP and stop_price is not None:
            req = StopOrderRequest(symbol=symbol, qty=qty, side=alpaca_side, time_in_force=alpaca_tif, stop_price=stop_price)  # type: ignore[assignment]
        else:
            raise BrokerError(f"Unsupported order type: {order_type}")

        result = client.submit_order(req)
        logger.info("Order placed: {} {} {} qty={}", side, order_type, symbol, qty)
        return Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=qty,
            time_in_force=time_in_force,
            limit_price=limit_price,
            stop_price=stop_price,
            status=OrderStatus(result.status.value),
            broker_id=str(result.id),
        )

    async def cancel_order(self, broker_id: str) -> None:
        client = self._require_client()
        client.cancel_order_by_id(broker_id)
        logger.info("Order cancelled: {}", broker_id)
