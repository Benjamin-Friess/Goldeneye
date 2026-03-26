"""Application-wide custom exceptions."""


class GoldeneyeError(Exception):
    """Base exception for all Goldeneye errors."""


class BrokerError(GoldeneyeError):
    """Raised when the broker API returns an unexpected result."""


class DataFeedError(GoldeneyeError):
    """Raised when the market data feed encounters an error."""


class BacktestError(GoldeneyeError):
    """Raised when the backtesting engine encounters an error."""


class ConfigError(GoldeneyeError):
    """Raised for invalid configuration."""
