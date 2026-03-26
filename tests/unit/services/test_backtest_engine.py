"""Tests for the backtesting engine using a simple buy-and-hold strategy."""

from datetime import datetime, timedelta

from goldeneye.models.bar import Bar
from goldeneye.models.order import Order, OrderSide, OrderType
from goldeneye.models.portfolio import Portfolio
from goldeneye.models.strategy import Strategy
from goldeneye.services.backtest.engine import BacktestEngine


def _make_bars(symbol: str, closes: list[float]) -> list[Bar]:
    base = datetime(2024, 1, 1)
    return [
        Bar(symbol=symbol, timestamp=base + timedelta(days=i),
            open=c, high=c + 1, low=c - 1, close=c, volume=1000)
        for i, c in enumerate(closes)
    ]


def _buy_first_bar_only(bar: Bar, portfolio: Portfolio) -> list[Order]:
    """Buy 1 share on the very first bar, hold forever."""
    if bar.symbol not in portfolio.positions and portfolio.cash > bar.close:
        return [Order(symbol=bar.symbol, side=OrderSide.BUY,
                      order_type=OrderType.MARKET, qty=1)]
    return []


def test_engine_buy_and_hold():
    bars = _make_bars("TEST", [100.0, 110.0, 120.0, 130.0])
    engine = BacktestEngine()
    result = engine.run(
        strategy=Strategy(name="BuyAndHold"),
        strategy_fn=_buy_first_bar_only,
        bars=bars,
        initial_cash=10_000.0,
    )
    assert result.num_trades == 1
    # Equity should have grown
    assert result.equity_curve[-1][1] > result.equity_curve[0][1]
    assert result.total_return > 0


def test_engine_no_bars_raises():
    import pytest
    from goldeneye.core.exceptions import BacktestError
    engine = BacktestEngine()
    with pytest.raises(BacktestError):
        engine.run(Strategy(name="Empty"), lambda b, p: [], bars=[])
