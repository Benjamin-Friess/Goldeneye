"""Chart panel: candlestick chart using pyqtgraph."""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from goldeneye.models.bar import Bar
from goldeneye.viewmodels.chart_vm import ChartViewModel


class ChartPanel(QWidget):
    def __init__(self, vm: ChartViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm

        self._plot_widget = pg.PlotWidget(self)
        self._plot_widget.setBackground("k")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot_widget)

        self._vm.bars_loaded.connect(self._on_bars_loaded)
        self._vm.bar_appended.connect(self._on_bar_appended)

        self._bars: list[Bar] = []

    def _on_bars_loaded(self, bars: list[Bar]) -> None:
        self._bars = bars
        self._redraw()

    def _on_bar_appended(self, bar: Bar) -> None:
        self._bars.append(bar)
        self._redraw()

    def _redraw(self) -> None:
        self._plot_widget.clear()
        if not self._bars:
            return

        closes = np.array([b.close for b in self._bars])
        xs = np.arange(len(closes))

        pen = pg.mkPen(color=(0, 200, 100), width=1)
        self._plot_widget.plot(xs, closes, pen=pen)
