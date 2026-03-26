"""
Main application window.

Uses QMainWindow with QDockWidget panels – panels can be floated,
moved, stacked, and tabbed exactly like GIMP's detachable windows.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QStatusBar,
)

from goldeneye.viewmodels.backtest_vm import BacktestViewModel
from goldeneye.viewmodels.chart_vm import ChartViewModel
from goldeneye.viewmodels.main_vm import MainViewModel
from goldeneye.viewmodels.orders_vm import OrdersViewModel
from goldeneye.viewmodels.portfolio_vm import PortfolioViewModel
from goldeneye.viewmodels.top100_vm import Top100ViewModel
from goldeneye.views.panels.backtest_panel import BacktestPanel
from goldeneye.views.panels.chart_panel import ChartPanel
from goldeneye.views.panels.multi_chart_panel import MultiChartWindow
from goldeneye.views.panels.order_panel import OrderPanel
from goldeneye.views.panels.portfolio_panel import PortfolioPanel
from goldeneye.views.panels.top100_panel import Top100Panel
from goldeneye.views.panels.watchlist_panel import WatchlistPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Goldeneye – Trading")
        self.resize(1600, 900)

        # ViewModels
        self._main_vm = MainViewModel(self)
        self._chart_vm = ChartViewModel(self)
        self._portfolio_vm = PortfolioViewModel(self._main_vm.broker, self)
        self._orders_vm = OrdersViewModel(self._main_vm.broker, self)
        self._backtest_vm = BacktestViewModel(self)
        self._top100_vm = Top100ViewModel(self)

        # Central widget: chart
        chart_panel = ChartPanel(self._chart_vm, self)
        self.setCentralWidget(chart_panel)

        # Multi-symbol chart (floating window, created once, shown on demand)
        self._multi_chart = MultiChartWindow(self._top100_vm, self)

        # Top 100 panel
        top100_panel = Top100Panel(self._top100_vm, self)
        top100_panel.chart_requested.connect(self._multi_chart.request)

        # Dockable panels
        self._add_dock("Top 100 Stocks", top100_panel, Qt.DockWidgetArea.LeftDockWidgetArea)
        self._add_dock("Watchlist", WatchlistPanel(self._main_vm, self), Qt.DockWidgetArea.LeftDockWidgetArea)
        self._add_dock("Portfolio", PortfolioPanel(self._portfolio_vm, self), Qt.DockWidgetArea.RightDockWidgetArea)
        self._add_dock("Orders", OrderPanel(self._orders_vm, self), Qt.DockWidgetArea.BottomDockWidgetArea)
        self._add_dock("Backtest", BacktestPanel(self._backtest_vm, self), Qt.DockWidgetArea.RightDockWidgetArea)

        # Status bar
        self._status = QStatusBar(self)
        self.setStatusBar(self._status)
        self._main_vm.status_message.connect(self._status.showMessage)
        self._main_vm.connected.connect(self._on_connected)

        self._restore_layout()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _add_dock(self, title: str, widget: object, area: Qt.DockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setObjectName(title)
        dock.setWidget(widget)  # type: ignore[arg-type]
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(area, dock)
        return dock

    def _restore_layout(self) -> None:
        from PyQt6.QtCore import QSettings
        settings = QSettings("Benjamin-Friess", "Goldeneye")
        state = settings.value("windowState")
        geo = settings.value("windowGeometry")
        if state:
            self.restoreState(state)  # type: ignore[arg-type]
        if geo:
            self.restoreGeometry(geo)  # type: ignore[arg-type]

    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        from PyQt6.QtCore import QSettings
        settings = QSettings("Benjamin-Friess", "Goldeneye")
        settings.setValue("windowState", self.saveState())
        settings.setValue("windowGeometry", self.saveGeometry())
        self._main_vm.stop_feed()
        super().closeEvent(event)  # type: ignore[arg-type]

    def _on_connected(self, ok: bool) -> None:
        msg = "● Connected" if ok else "○ Disconnected"
        self.statusBar().showMessage(msg)
