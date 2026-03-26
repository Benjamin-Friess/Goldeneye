"""
In-process event bus using Qt signals.

Components publish typed events; subscribers connect via Qt's signal/slot
mechanism so cross-thread delivery is safe.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    """Singleton event bus for application-wide messaging."""

    # Market data
    quote_received = pyqtSignal(object)   # models.Quote
    bar_received = pyqtSignal(object)     # models.Bar

    # Orders & positions
    order_updated = pyqtSignal(object)    # models.Order
    position_updated = pyqtSignal(object) # models.Position

    # Backtest
    backtest_progress = pyqtSignal(int)   # percent 0-100
    backtest_complete = pyqtSignal(object) # services.backtest.BacktestResult

    # UI
    symbol_selected = pyqtSignal(str)

    _instance: "EventBus | None" = None

    @classmethod
    def instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


bus = EventBus.instance()
