"""
Backtesting engine.

Feed historical bars through a strategy callable and collect fills,
equity curve, and performance metrics.
"""

from dataclasses import dataclass, field
from typing import Callable

from goldeneye.core.exceptions import BacktestError
from goldeneye.models.bar import Bar
from goldeneye.models.order import Order, OrderSide, OrderStatus, OrderType, TimeInForce
from goldeneye.models.portfolio import Portfolio
from goldeneye.models.position import Position
from goldeneye.models.strategy import Strategy


# A strategy function receives the current bar and the portfolio, then returns
# a list of orders to place (or an empty list to hold).
StrategyFn = Callable[[Bar, Portfolio], list[Order]]


@dataclass
class BacktestResult:
    strategy: Strategy
    symbol: str
    equity_curve: list[tuple[object, float]] = field(default_factory=list)  # (datetime, equity)
    trades: list[Order] = field(default_factory=list)
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    num_trades: int = 0


class BacktestEngine:
    """Event-driven backtester: one bar at a time, no lookahead."""

    def run(
        self,
        strategy: Strategy,
        strategy_fn: StrategyFn,
        bars: list[Bar],
        initial_cash: float = 100_000.0,
        progress_cb: Callable[[int], None] | None = None,
    ) -> BacktestResult:
        if not bars:
            raise BacktestError("No bars provided for backtesting.")

        symbol = bars[0].symbol
        portfolio = Portfolio(cash=initial_cash)
        result = BacktestResult(strategy=strategy, symbol=symbol)
        total = len(bars)

        for i, bar in enumerate(bars):
            # Update current prices
            if symbol in portfolio.positions:
                portfolio.positions[symbol].current_price = bar.close

            orders = strategy_fn(bar, portfolio)
            for order in orders:
                self._fill_order(order, bar, portfolio)
                result.trades.append(order)

            equity = portfolio.equity
            result.equity_curve.append((bar.timestamp, equity))

            if progress_cb and i % max(1, total // 100) == 0:
                progress_cb(int(i / total * 100))

        if progress_cb:
            progress_cb(100)

        result.num_trades = len(result.trades)
        result.total_return = self._total_return(result.equity_curve, initial_cash)
        result.max_drawdown = self._max_drawdown(result.equity_curve)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fill_order(self, order: Order, bar: Bar, portfolio: Portfolio) -> None:
        fill_price = bar.close
        if order.order_type == OrderType.LIMIT and order.limit_price is not None:
            if order.side == OrderSide.BUY and bar.low > order.limit_price:
                return  # not triggered
            if order.side == OrderSide.SELL and bar.high < order.limit_price:
                return
            fill_price = order.limit_price

        cost = fill_price * order.qty
        if order.side == OrderSide.BUY:
            if portfolio.cash < cost:
                return  # insufficient funds
            portfolio.cash -= cost
            pos = portfolio.positions.get(order.symbol)
            if pos:
                total_qty = pos.qty + order.qty
                pos.avg_entry_price = (pos.avg_entry_price * pos.qty + cost) / total_qty
                pos.qty = total_qty
            else:
                portfolio.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    qty=order.qty,
                    avg_entry_price=fill_price,
                    current_price=fill_price,
                )
        else:  # SELL
            pos = portfolio.positions.get(order.symbol)
            if not pos or pos.qty < order.qty:
                return  # nothing to sell
            portfolio.cash += cost
            pos.qty -= order.qty
            if pos.qty == 0:
                del portfolio.positions[order.symbol]

        order.status = OrderStatus.FILLED
        order.filled_avg_price = fill_price
        order.filled_qty = order.qty

    @staticmethod
    def _total_return(curve: list[tuple[object, float]], initial: float) -> float:
        if not curve or initial == 0:
            return 0.0
        return (curve[-1][1] - initial) / initial

    @staticmethod
    def _max_drawdown(curve: list[tuple[object, float]]) -> float:
        if not curve:
            return 0.0
        peak = curve[0][1]
        max_dd = 0.0
        for _, equity in curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)
        return max_dd
