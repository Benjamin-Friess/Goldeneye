"""Backtest panel: configure and run a backtest, display results."""

from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from goldeneye.models.bar import Bar
from goldeneye.models.order import Order, OrderSide, OrderType
from goldeneye.models.portfolio import Portfolio
from goldeneye.models.strategy import Strategy
from goldeneye.services.backtest.engine import BacktestResult
from goldeneye.services.data.historical import HistoricalDataLoader
from goldeneye.viewmodels.backtest_vm import BacktestViewModel


def _simple_ma_crossover(bar: Bar, portfolio: Portfolio) -> list[Order]:
    """Built-in demo strategy: placeholder (no state here – real strategies use a class)."""
    return []


class BacktestPanel(QWidget):
    def __init__(self, vm: BacktestViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm
        self._loader = HistoricalDataLoader()

        self._symbol_edit = QLineEdit(self)
        self._symbol_edit.setPlaceholderText("AAPL")
        self._cash_spin = QDoubleSpinBox(self)
        self._cash_spin.setRange(1_000, 10_000_000)
        self._cash_spin.setValue(100_000)
        self._cash_spin.setPrefix("$")
        self._run_btn = QPushButton("Run Backtest", self)
        self._progress = QProgressBar(self)
        self._results = QTextEdit(self)
        self._results.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Symbol", self._symbol_edit)
        form.addRow("Initial Cash", self._cash_spin)

        config_box = QGroupBox("Configuration", self)
        config_layout = QVBoxLayout(config_box)
        config_layout.addLayout(form)
        config_layout.addWidget(self._run_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(config_box)
        layout.addWidget(self._progress)
        layout.addWidget(QLabel("Results:", self))
        layout.addWidget(self._results)

        self._run_btn.clicked.connect(self._run)
        self._vm.progress_updated.connect(self._progress.setValue)
        self._vm.result_ready.connect(self._show_result)
        self._vm.error_occurred.connect(lambda e: self._results.setPlainText(f"Error: {e}"))

    def _run(self) -> None:
        from datetime import datetime, timedelta
        symbol = self._symbol_edit.text().strip().upper()
        if not symbol:
            return
        end = datetime.utcnow()
        start = end - timedelta(days=365)
        try:
            bars = self._loader.get_bars(symbol, start, end)
        except Exception as exc:
            self._results.setPlainText(f"Data load error: {exc}")
            return

        strategy = Strategy(name="MA Crossover Demo")
        self._vm.run(strategy, _simple_ma_crossover, bars, self._cash_spin.value())

    def _show_result(self, result: BacktestResult) -> None:
        text = (
            f"Strategy : {result.strategy.name}\n"
            f"Symbol   : {result.symbol}\n"
            f"Trades   : {result.num_trades}\n"
            f"Return   : {result.total_return:.2%}\n"
            f"Max DD   : {result.max_drawdown:.2%}\n"
        )
        self._results.setPlainText(text)
