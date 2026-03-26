"""ViewModel: backtesting configuration and results."""

import threading
from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal

from goldeneye.models.bar import Bar
from goldeneye.models.portfolio import Portfolio
from goldeneye.models.strategy import Strategy
from goldeneye.services.backtest.engine import BacktestEngine, BacktestResult


class BacktestViewModel(QObject):
    progress_updated = pyqtSignal(int)       # 0-100
    result_ready = pyqtSignal(object)        # BacktestResult
    error_occurred = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._engine = BacktestEngine()

    def run(
        self,
        strategy: Strategy,
        strategy_fn: Callable[[Bar, Portfolio], list],
        bars: list[Bar],
        initial_cash: float = 100_000.0,
    ) -> None:
        thread = threading.Thread(
            target=self._run_in_thread,
            args=(strategy, strategy_fn, bars, initial_cash),
            daemon=True,
        )
        thread.start()

    def _run_in_thread(
        self,
        strategy: Strategy,
        strategy_fn: Callable,
        bars: list[Bar],
        initial_cash: float,
    ) -> None:
        try:
            result: BacktestResult = self._engine.run(
                strategy=strategy,
                strategy_fn=strategy_fn,
                bars=bars,
                initial_cash=initial_cash,
                progress_cb=lambda p: self.progress_updated.emit(p),
            )
            self.result_ready.emit(result)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
