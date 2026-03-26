"""Portfolio panel: positions table."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from goldeneye.models.portfolio import Portfolio
from goldeneye.viewmodels.portfolio_vm import PortfolioViewModel

_HEADERS = ["Symbol", "Qty", "Avg Entry", "Current", "Market Value", "Unrealized P&L", "P&L %"]


class PortfolioPanel(QWidget):
    def __init__(self, vm: PortfolioViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm

        self._table = QTableWidget(0, len(_HEADERS), self)
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        refresh_btn = QPushButton("Refresh", self)
        refresh_btn.clicked.connect(self._vm.refresh)

        layout = QVBoxLayout(self)
        layout.addWidget(refresh_btn)
        layout.addWidget(self._table)

        self._vm.portfolio_updated.connect(self._update_table)

    def _update_table(self, portfolio: Portfolio) -> None:
        positions = list(portfolio.positions.values())
        self._table.setRowCount(len(positions))
        for row, pos in enumerate(positions):
            data = [
                pos.symbol,
                f"{pos.qty:.4f}",
                f"{pos.avg_entry_price:.2f}",
                f"{pos.current_price:.2f}",
                f"{pos.market_value:.2f}",
                f"{pos.unrealized_pnl:.2f}",
                f"{pos.unrealized_pnl_pct:.2%}",
            ]
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._table.setItem(row, col, item)
