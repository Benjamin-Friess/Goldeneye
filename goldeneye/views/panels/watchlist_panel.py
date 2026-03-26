"""Watchlist panel: list of tracked symbols with live bid/ask."""

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from goldeneye.core.events import bus
from goldeneye.viewmodels.main_vm import MainViewModel


class WatchlistPanel(QWidget):
    def __init__(self, vm: MainViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm

        self._list = QListWidget(self)
        self._entry = QLineEdit(self)
        self._entry.setPlaceholderText("Symbol (e.g. AAPL)")
        self._add_btn = QPushButton("Add", self)
        self._connect_btn = QPushButton("Connect", self)

        row = QHBoxLayout()
        row.addWidget(self._entry)
        row.addWidget(self._add_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._connect_btn)
        layout.addLayout(row)
        layout.addWidget(self._list)

        self._add_btn.clicked.connect(self._add_symbol)
        self._connect_btn.clicked.connect(self._connect)
        self._list.itemDoubleClicked.connect(
            lambda item: bus.symbol_selected.emit(item.text().split()[0])
        )

    def _add_symbol(self) -> None:
        sym = self._entry.text().strip().upper()
        if sym:
            self._list.addItem(sym)
            self._entry.clear()

    def _connect(self) -> None:
        symbols = [self._list.item(i).text() for i in range(self._list.count())]
        if symbols:
            self._vm.connect_broker()
            self._vm.start_feed(symbols)
