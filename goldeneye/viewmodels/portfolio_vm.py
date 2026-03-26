"""ViewModel: portfolio positions and account equity."""

import asyncio

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from goldeneye.models.portfolio import Portfolio
from goldeneye.services.broker.base import BrokerBase


class PortfolioViewModel(QObject):
    portfolio_updated = pyqtSignal(object)  # Portfolio

    def __init__(self, broker: BrokerBase, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._broker = broker
        self.portfolio = Portfolio()

    def refresh(self) -> None:
        asyncio.run(self._async_refresh())

    async def _async_refresh(self) -> None:
        try:
            self.portfolio = await self._broker.get_portfolio()
            self.portfolio_updated.emit(self.portfolio)
        except Exception as exc:
            logger.error("Portfolio refresh failed: {}", exc)
