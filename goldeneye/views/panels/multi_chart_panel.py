"""
Multi-symbol chart panel.

Shows price evolution (normalised to % change from period start) for one or
more symbols over a chosen time range. Opens as a floating QDialog so it
does not displace the main layout.
"""

from datetime import datetime

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from goldeneye.models.bar import Bar
from goldeneye.viewmodels.top100_vm import TIME_RANGES, Top100ViewModel

# Palette for up to 10 lines
_PALETTE = [
    "#00C864",  # green
    "#2196F3",  # blue
    "#FF5722",  # orange-red
    "#FFC107",  # amber
    "#9C27B0",  # purple
    "#00BCD4",  # cyan
    "#F06292",  # pink
    "#8BC34A",  # light green
    "#FF9800",  # orange
    "#607D8B",  # blue-grey
]


class MultiChartWindow(QDialog):
    """Floating window with a pyqtgraph chart for multiple symbols."""

    def __init__(self, vm: Top100ViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Price Evolution")
        self.resize(900, 500)
        self.setWindowFlag(Qt.WindowType.Window)  # fully independent window

        self._vm = vm

        self._title_label = QLabel("", self)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._plot = pg.PlotWidget(self)
        self._plot.setBackground("#1a1a2e")
        self._plot.showGrid(x=True, y=True, alpha=0.25)
        self._plot.setLabel("left", "% change from start")
        self._plot.setLabel("bottom", "Bar index")
        self._legend = self._plot.addLegend(offset=(10, 10))

        self._loading_label = QLabel("", self)
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._plot)
        layout.addWidget(self._loading_label)

        self._vm.data_ready.connect(self._on_data_ready)
        self._vm.loading.connect(self._on_loading)
        self._vm.error_occurred.connect(lambda e: self._loading_label.setText(f"Error: {e}"))

    # ------------------------------------------------------------------

    def request(self, symbols: list[str], range_key: str) -> None:
        """Called by the main window to trigger a new data fetch."""
        label = TIME_RANGES[range_key][2]
        self._title_label.setText(
            f"{', '.join(symbols)}  –  {range_key}  ({label} bars)"
        )
        self._plot.clear()
        self._legend.clear()
        self._loading_label.setText("Fetching data…")
        self.show()
        self.raise_()
        self._vm.load_chart_data(symbols, range_key)

    # ------------------------------------------------------------------

    @pyqtSlot(bool)
    def _on_loading(self, on: bool) -> None:
        self._loading_label.setText("Loading…" if on else "")

    @pyqtSlot(dict)
    def _on_data_ready(self, data: dict) -> None:
        self._plot.clear()
        self._legend.clear()
        self._loading_label.setText("")

        for i, (symbol, bars) in enumerate(data.items()):
            if not bars:
                continue
            closes = np.array([b.close for b in bars], dtype=float)
            if closes[0] == 0:
                continue
            # Normalise: % change from first close
            pct = (closes / closes[0] - 1.0) * 100.0
            xs = np.arange(len(pct))

            color = _PALETTE[i % len(_PALETTE)]
            pen = pg.mkPen(color=color, width=2)
            curve = self._plot.plot(xs, pct, pen=pen, name=symbol)
