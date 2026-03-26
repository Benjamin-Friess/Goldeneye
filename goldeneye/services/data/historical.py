"""Historical OHLCV data loader via Alpaca REST API."""

from datetime import datetime

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from loguru import logger

from goldeneye.core.config import settings
from goldeneye.core.exceptions import DataFeedError
from goldeneye.models.bar import Bar


class HistoricalDataLoader:
    def __init__(self) -> None:
        self._client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
        )

    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.Day,
    ) -> list[Bar]:
        logger.info("Fetching historical bars: {} {} → {}", symbol, start.date(), end.date())
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
            )
            response = self._client.get_stock_bars(request)
            bars_df: pd.DataFrame = response.df

            if bars_df.empty:
                return []

            bars_df = bars_df.reset_index()
            return [
                Bar(
                    symbol=symbol,
                    timestamp=row["timestamp"].to_pydatetime(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"]),
                    vwap=float(row.get("vwap", 0.0)),
                )
                for _, row in bars_df.iterrows()
            ]
        except Exception as exc:
            raise DataFeedError(f"Failed to fetch bars for {symbol}: {exc}") from exc
