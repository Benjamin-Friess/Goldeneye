"""ViewModel: candlestick chart data for a given symbol."""

from datetime import datetime, timedelta

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from loguru import logger

from goldeneye.core.events import bus
from goldeneye.models.bar import Bar
from goldeneye.services.data.historical import HistoricalDataLoader


class ChartViewModel(QObject):
    bars_loaded = pyqtSignal(list)   # list[Bar]
    bar_appended = pyqtSignal(object)  # Bar

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._loader = HistoricalDataLoader()
        self._symbol = ""
        self._bars: list[Bar] = []

        bus.bar_received.connect(self._on_live_bar)
        bus.symbol_selected.connect(self.load_symbol)

    @pyqtSlot(str)
    def load_symbol(self, symbol: str) -> None:
        self._symbol = symbol
        end = datetime.utcnow()
        start = end - timedelta(days=365)
        try:
            self._bars = self._loader.get_bars(symbol, start, end)
            self.bars_loaded.emit(self._bars)
        except Exception as exc:
            logger.error("Chart load failed for {}: {}", symbol, exc)

    @pyqtSlot(object)
    def _on_live_bar(self, bar: Bar) -> None:
        if bar.symbol == self._symbol:
            self._bars.append(bar)
            self.bar_appended.emit(bar)
