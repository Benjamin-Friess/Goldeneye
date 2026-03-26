"""
Top 100 stocks panel.

Displays an S&P 100 table with multi-select. On selection + time-range choice,
emits a signal that opens / updates the MultiChartPanel.
"""

import math

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
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

_HEADERS = ["Symbol", "Company", "Spread ($)", "Accum. Gain % (1M)"]
_RANGE_KEYS = list(TIME_RANGES.keys())


class Top100Panel(QWidget):
    """Emits chart_requested(symbols, range_key) when the user makes a selection."""

    chart_requested = pyqtSignal(list, str)   # list[str], range_key

    def __init__(self, vm: Top100ViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm
        self._current_range = "1M"
        # Cache of symbol → spread / momentum so filter rebuilds can re-apply values
        self._spread_cache: dict[str, float] = {}
        self._momentum_cache: dict[str, float] = {}

        # ── Search bar ────────────────────────────────────────────────
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Filter…")
        self._search.textChanged.connect(self._apply_filter)

        # ── Table ─────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(_HEADERS), self)
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.verticalHeader().setVisible(False)
        self._populate()

        # ── Refresh spreads button ────────────────────────────────────
        self._refresh_btn = QPushButton("↻ Refresh Spreads", self)
        self._refresh_btn.clicked.connect(self._refresh_spreads)

        # ── Refresh momentum button ───────────────────────────────────
        self._momentum_btn = QPushButton("↻ Refresh Momentum", self)
        self._momentum_btn.clicked.connect(self._refresh_momentum)

        refresh_row = QHBoxLayout()
        refresh_row.addWidget(self._refresh_btn)
        refresh_row.addWidget(self._momentum_btn)

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
        self._vm.spreads_ready.connect(self._on_spreads_ready)
        self._vm.momentum_ready.connect(self._on_momentum_ready)

        # ── Layout ────────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.addWidget(self._search)
        layout.addWidget(self._table)
        layout.addLayout(refresh_row)
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
        # Sort by descending momentum; symbols with no data go to the bottom
        rows.sort(
            key=lambda x: self._momentum_cache.get(x[0], float("-inf")),
            reverse=True,
        )
        self._table.setRowCount(len(rows))
        for r, (sym, name) in enumerate(rows):
            sym_item = QTableWidgetItem(sym)
            sym_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(r, 0, sym_item)
            self._table.setItem(r, 1, QTableWidgetItem(name))

            # Spread column
            spread_val = self._spread_cache.get(sym)
            spread_item = QTableWidgetItem(
                f"{spread_val:.4f}" if spread_val is not None and not math.isnan(spread_val) else "—"
            )
            spread_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(r, 2, spread_item)

            # Momentum column
            mom_val = self._momentum_cache.get(sym)
            mom_item = QTableWidgetItem(
                f"{mom_val:.2f} %" if mom_val is not None and not math.isnan(mom_val) else "—"
            )
            mom_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(r, 3, mom_item)

    def _apply_filter(self, text: str) -> None:
        self._populate(text)

    def _set_range(self, key: str) -> None:
        self._current_range = key
        for k, btn in self._range_btns.items():
            btn.setChecked(k == key)

    def _refresh_spreads(self) -> None:
        self._refresh_btn.setEnabled(False)
        self._status.setText("Fetching spreads…")
        self._vm.refresh_spreads()

    def _refresh_momentum(self) -> None:
        self._momentum_btn.setEnabled(False)
        self._status.setText("Fetching momentum (this may take a few seconds)…")
        self._vm.refresh_momentum()

    @pyqtSlot(dict)
    def _on_spreads_ready(self, spreads: dict) -> None:
        self._spread_cache.update(spreads)
        self._refresh_btn.setEnabled(True)
        self._status.setText("Spreads updated.")
        # Update visible rows without full repopulate (preserves selection)
        for r in range(self._table.rowCount()):
            sym_item = self._table.item(r, 0)
            if sym_item is None:
                continue
            sym = sym_item.text()
            spread_val = self._spread_cache.get(sym)
            spread_item = QTableWidgetItem(
                f"{spread_val:.4f}" if spread_val is not None and not math.isnan(spread_val) else "—"
            )
            spread_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(r, 2, spread_item)

    @pyqtSlot(dict)
    def _on_momentum_ready(self, momentum: dict) -> None:
        self._momentum_cache.update(momentum)
        self._momentum_btn.setEnabled(True)
        self._status.setText("Momentum updated — table sorted by accumulated gain.")
        # Full repopulate to apply new sort order
        self._populate(self._search.text())

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
