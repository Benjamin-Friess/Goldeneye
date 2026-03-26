"""Order panel: order blotter + order entry form."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from goldeneye.models.order import Order, OrderSide, OrderType, TimeInForce
from goldeneye.viewmodels.orders_vm import OrdersViewModel

_HEADERS = ["ID", "Symbol", "Side", "Type", "Qty", "Status", "Fill Price"]


class OrderPanel(QWidget):
    def __init__(self, vm: OrdersViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm

        # Blotter
        self._table = QTableWidget(0, len(_HEADERS), self)
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)

        # Order entry
        self._symbol_edit = QLineEdit(self)
        self._symbol_edit.setPlaceholderText("AAPL")
        self._side_combo = QComboBox(self)
        self._side_combo.addItems(["buy", "sell"])
        self._type_combo = QComboBox(self)
        self._type_combo.addItems(["market", "limit", "stop"])
        self._qty_spin = QDoubleSpinBox(self)
        self._qty_spin.setRange(0.001, 100_000)
        self._qty_spin.setValue(1)
        self._limit_spin = QDoubleSpinBox(self)
        self._limit_spin.setRange(0, 1_000_000)
        self._limit_spin.setPrefix("$")
        self._submit_btn = QPushButton("Place Order", self)
        self._submit_btn.clicked.connect(self._place_order)

        form = QFormLayout()
        form.addRow("Symbol", self._symbol_edit)
        form.addRow("Side", self._side_combo)
        form.addRow("Type", self._type_combo)
        form.addRow("Qty", self._qty_spin)
        form.addRow("Limit/Stop $", self._limit_spin)

        entry_box = QGroupBox("New Order", self)
        entry_layout = QVBoxLayout(entry_box)
        entry_layout.addLayout(form)
        entry_layout.addWidget(self._submit_btn)

        self._status_label = QLabel("", self)

        layout = QVBoxLayout(self)
        layout.addWidget(entry_box)
        layout.addWidget(self._status_label)
        layout.addWidget(self._table)

        self._vm.orders_updated.connect(self._refresh_table)
        self._vm.order_placed.connect(lambda o: self._vm.refresh())
        self._vm.error_occurred.connect(lambda e: self._status_label.setText(f"Error: {e}"))

    def _place_order(self) -> None:
        symbol = self._symbol_edit.text().strip().upper()
        if not symbol:
            return
        side = OrderSide(self._side_combo.currentText())
        order_type = OrderType(self._type_combo.currentText())
        qty = self._qty_spin.value()
        limit_price = self._limit_spin.value() if order_type != OrderType.MARKET else None
        self._vm.place_order(symbol, side, order_type, qty, limit_price=limit_price)

    def _refresh_table(self, orders: list[Order]) -> None:
        self._table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            data = [
                order.broker_id[:8],
                order.symbol,
                order.side.value,
                order.order_type.value,
                f"{order.qty:.4f}",
                order.status.value,
                f"{order.filled_avg_price:.2f}" if order.filled_avg_price else "–",
            ]
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._table.setItem(row, col, item)
