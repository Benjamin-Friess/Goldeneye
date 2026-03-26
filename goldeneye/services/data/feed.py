"""Real-time market data feed via Alpaca WebSocket."""

from alpaca.data.live import StockDataStream
from loguru import logger

from goldeneye.core.config import settings
from goldeneye.core.events import bus
from goldeneye.models.bar import Bar
from goldeneye.models.quote import Quote


class DataFeed:
    """Subscribes to real-time quotes and minute bars for a set of symbols."""

    def __init__(self) -> None:
        self._stream: StockDataStream | None = None
        self._subscribed_symbols: set[str] = set()

    def start(self, symbols: list[str]) -> None:
        self._stream = StockDataStream(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            feed="iex",  # free tier; use "sip" for paid
        )
        self._subscribed_symbols = set(symbols)
        self._stream.subscribe_quotes(self._on_quote, *symbols)
        self._stream.subscribe_bars(self._on_bar, *symbols)
        logger.info("DataFeed starting for: {}", symbols)
        self._stream.run()  # blocking – run in a thread

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream = None

    async def _on_quote(self, data: object) -> None:  # type: ignore[override]
        try:
            q = Quote(
                symbol=data.symbol,          # type: ignore[attr-defined]
                bid=float(data.bid_price),   # type: ignore[attr-defined]
                ask=float(data.ask_price),   # type: ignore[attr-defined]
                bid_size=int(data.bid_size), # type: ignore[attr-defined]
                ask_size=int(data.ask_size), # type: ignore[attr-defined]
                timestamp=data.timestamp,    # type: ignore[attr-defined]
            )
            bus.quote_received.emit(q)
        except Exception as exc:
            logger.warning("Quote parse error: {}", exc)

    async def _on_bar(self, data: object) -> None:  # type: ignore[override]
        try:
            b = Bar(
                symbol=data.symbol,          # type: ignore[attr-defined]
                timestamp=data.timestamp,    # type: ignore[attr-defined]
                open=float(data.open),       # type: ignore[attr-defined]
                high=float(data.high),       # type: ignore[attr-defined]
                low=float(data.low),         # type: ignore[attr-defined]
                close=float(data.close),     # type: ignore[attr-defined]
                volume=int(data.volume),     # type: ignore[attr-defined]
                vwap=float(data.vwap) if hasattr(data, "vwap") else 0.0,
            )
            bus.bar_received.emit(b)
        except Exception as exc:
            logger.warning("Bar parse error: {}", exc)
