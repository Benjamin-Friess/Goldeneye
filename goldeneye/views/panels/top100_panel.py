"""
Top 100 stocks panel.

Displays an S&P 100 table with multi-select. On selection + time-range choice,
emits a signal that opens / updates the MultiChartPanel.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from goldeneye.viewmodels.top100_vm import TIME_RANGES, Top100ViewModel

_HEADERS = ["Symbol", "Company"]
_RANGE_KEYS = list(TIME_RANGES.keys())   # ["1D", "5D", "1M", "3M", "6M", "1Y"]


class Top100Panel(QWidget):
    """Emits chart_requested(symbols, range_key) when the user makes a selection."""

    chart_requested = pyqtSignal(list, str)   # list[str], range_key

    def __init__(self, vm: Top100ViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm
        self._current_range = "1M"

        # ── Search bar ────────────────────────────────────────────────
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Filter…")
        self._search.textChanged.connect(self._apply_filter)

        # ── Table ─────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(_HEADERS), self)
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.verticalHeader().setVisible(False)
        self._populate()

        # ── Time-range buttons ────────────────────────────────────────
        self._range_btns: dict[str, QPushButton] = {}
        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Range:", self))
        for key in _RANGE_KEYS:
            btn = QPushButton(key, self)
            btn.setCheckable(True)
            btn.setChecked(key == self._current_range)
            btn.clicked.connect(lambda checked, k=key: self._set_range(k))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._range_btns[key] = btn
            range_row.addWidget(btn)

        # ── Show chart button ─────────────────────────────────────────
        self._show_btn = QPushButton("Show Chart", self)
        self._show_btn.clicked.connect(self._request_chart)

        # ── Status label ──────────────────────────────────────────────
        self._status = QLabel("Select one or more symbols, then click Show Chart.", self)
        self._status.setWordWrap(True)

        self._vm.loading.connect(lambda on: self._status.setText("Loading data…" if on else ""))
        self._vm.error_occurred.connect(self._status.setText)

        # ── Layout ────────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.addWidget(self._search)
        layout.addWidget(self._table)
        layout.addLayout(range_row)
        layout.addWidget(self._show_btn)
        layout.addWidget(self._status)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _populate(self, filter_text: str = "") -> None:
        ft = filter_text.lower()
        rows = [
            (sym, name) for sym, name in self._vm.symbols
            if ft in sym.lower() or ft in name.lower()
        ]
        self._table.setRowCount(len(rows))
        for r, (sym, name) in enumerate(rows):
            sym_item = QTableWidgetItem(sym)
            sym_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(r, 0, sym_item)
            self._table.setItem(r, 1, QTableWidgetItem(name))
        self._table.resizeColumnToContents(0)

    def _apply_filter(self, text: str) -> None:
        self._populate(text)

    def _set_range(self, key: str) -> None:
        self._current_range = key
        for k, btn in self._range_btns.items():
            btn.setChecked(k == key)

    def _request_chart(self) -> None:
        selected = list({
            self._table.item(idx.row(), 0).text()
            for idx in self._table.selectedIndexes()
        })
        if not selected:
            self._status.setText("Please select at least one symbol.")
            return
        self._status.setText(f"Loading {len(selected)} symbol(s)…")
        self.chart_requested.emit(selected, self._current_range)
