"""ViewModel: main application state (broker connection, watchlist)."""

import threading

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from loguru import logger

from goldeneye.core.events import bus
from goldeneye.models.quote import Quote
from goldeneye.services.broker.alpaca import AlpacaBroker
from goldeneye.services.data.feed import DataFeed


class MainViewModel(QObject):
    connected = pyqtSignal(bool)
    status_message = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.broker = AlpacaBroker()
        self.feed = DataFeed()
        self._watchlist: list[str] = []

    # ------------------------------------------------------------------
    # Public API called by the view
    # ------------------------------------------------------------------

    def connect_broker(self) -> None:
        import asyncio
        asyncio.run(self._async_connect())

    async def _async_connect(self) -> None:
        try:
            await self.broker.connect()
            self.connected.emit(True)
            self.status_message.emit("Connected to Alpaca")
        except Exception as exc:
            logger.error("Broker connection failed: {}", exc)
            self.connected.emit(False)
            self.status_message.emit(f"Connection failed: {exc}")

    def start_feed(self, symbols: list[str]) -> None:
        self._watchlist = symbols
        thread = threading.Thread(target=self.feed.start, args=(symbols,), daemon=True)
        thread.start()

    def stop_feed(self) -> None:
        self.feed.stop()

    @pyqtSlot(str)
    def on_symbol_selected(self, symbol: str) -> None:
        bus.symbol_selected.emit(symbol)
