"""ViewModel: Top 100 stocks table and multi-symbol chart data."""

import threading
from datetime import datetime, timedelta, timezone

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from loguru import logger

from goldeneye.core.config import settings
from goldeneye.models.bar import Bar
from goldeneye.services.data.historical import HistoricalDataLoader
from goldeneye.services.data.symbols import SP100

# Time-range presets: label → (delta, TimeFrame, bar_label)
TIME_RANGES: dict[str, tuple[timedelta, TimeFrame, str]] = {
    "1D":  (timedelta(days=1),   TimeFrame(5,  TimeFrameUnit.Minute), "5 min"),
    "5D":  (timedelta(days=5),   TimeFrame(1,  TimeFrameUnit.Hour),   "1 h"),
    "1M":  (timedelta(days=30),  TimeFrame.Day,                        "Daily"),
    "3M":  (timedelta(days=90),  TimeFrame.Day,                        "Daily"),
    "6M":  (timedelta(days=180), TimeFrame.Day,                        "Daily"),
    "1Y":  (timedelta(days=365), TimeFrame.Day,                        "Daily"),
}


class Top100ViewModel(QObject):
    """Manages the SP100 list and asynchronous multi-symbol historical loads."""

    data_ready      = pyqtSignal(dict)   # {symbol: list[Bar]}
    spreads_ready   = pyqtSignal(dict)   # {symbol: float}  bid-ask spread in $
    momentum_ready  = pyqtSignal(dict)   # {symbol: float}  accumulated positive variation %
    loading         = pyqtSignal(bool)
    error_occurred  = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._loader = HistoricalDataLoader()
        self.symbols: list[tuple[str, str]] = SP100  # (ticker, name)
        self._feed = DataFeed.SIP if settings.alpaca_feed == "sip" else DataFeed.IEX
        self._client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
        )

    # ------------------------------------------------------------------
    # Chart data
    # ------------------------------------------------------------------

    def load_chart_data(self, symbols: list[str], range_key: str) -> None:
        """Fetch historical bars for *symbols* over the given time range (non-blocking)."""
        thread = threading.Thread(
            target=self._fetch, args=(symbols, range_key), daemon=True
        )
        thread.start()

    def _fetch(self, symbols: list[str], range_key: str) -> None:
        self.loading.emit(True)
        delta, timeframe, _ = TIME_RANGES[range_key]
        end = datetime.now(tz=timezone.utc)
        start = end - delta

        result: dict[str, list[Bar]] = {}
        for sym in symbols:
            try:
                bars = self._loader.get_bars(sym, start, end, timeframe)
                result[sym] = bars
            except Exception as exc:
                logger.warning("Failed to load {} : {}", sym, exc)

        self.loading.emit(False)
        if result:
            self.data_ready.emit(result)
        else:
            self.error_occurred.emit("No data returned for selected symbols.")

    # ------------------------------------------------------------------
    # Spread data
    # ------------------------------------------------------------------

    def refresh_spreads(self) -> None:
        """Fetch latest bid/ask quotes for all SP100 symbols (non-blocking)."""
        thread = threading.Thread(target=self._fetch_spreads, daemon=True)
        thread.start()

    def _fetch_spreads(self) -> None:
        try:
            tickers = [sym for sym, _ in self.symbols]
            request = StockLatestQuoteRequest(symbol_or_symbols=tickers, feed=self._feed)
            response = self._client.get_stock_latest_quote(request)

            spreads: dict[str, float] = {}
            for sym, quote in response.items():
                try:
                    bid = float(quote.bid_price)
                    ask = float(quote.ask_price)
                    spreads[sym] = (ask - bid) if bid > 0 and ask > bid else float("nan")
                except Exception:
                    spreads[sym] = float("nan")

            self.spreads_ready.emit(spreads)
        except Exception as exc:
            logger.warning("Spread fetch failed: {}", exc)

    # ------------------------------------------------------------------
    # Momentum: accumulated positive variation (1-hour bars, last 30 days)
    # ------------------------------------------------------------------

    def refresh_momentum(self) -> None:
        """Fetch 1-hour bars for all SP100 symbols and compute accumulated
        positive variation (sum of positive bar-to-bar % changes) over
        the last 30 days. Non-blocking."""
        thread = threading.Thread(target=self._fetch_momentum, daemon=True)
        thread.start()

    def _fetch_momentum(self) -> None:
        try:
            tickers = [sym for sym, _ in self.symbols]
            end = datetime.now(tz=timezone.utc)
            start = end - timedelta(days=30)

            # Batch request: all symbols in one API call
            request = StockBarsRequest(
                symbol_or_symbols=tickers,
                timeframe=TimeFrame(1, TimeFrameUnit.Hour),
                start=start,
                end=end,
                feed=self._feed,
            )
            response = self._client.get_stock_bars(request)
            bars_df = response.df  # MultiIndex: (symbol, timestamp)

            momentum: dict[str, float] = {}
            for sym in tickers:
                try:
                    closes = bars_df.loc[sym]["close"].values.astype(float)
                    if len(closes) < 2:
                        momentum[sym] = float("nan")
                        continue
                    # Bar-to-bar % changes, keep only positive ones
                    pct_changes = np.diff(closes) / closes[:-1] * 100.0
                    momentum[sym] = float(np.sum(pct_changes[pct_changes > 0]))
                except KeyError:
                    momentum[sym] = float("nan")
                except Exception as exc:
                    logger.warning("Momentum calc failed for {}: {}", sym, exc)
                    momentum[sym] = float("nan")

            self.momentum_ready.emit(momentum)
        except Exception as exc:
            logger.warning("Momentum fetch failed: {}", exc)
            self.error_occurred.emit(f"Momentum fetch failed: {exc}")

