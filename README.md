# Goldeneye

> A professional stock trading application built with Python, PyQt6, and Alpaca.

## Features

- 📊 Real-time stock quotes and candlestick charts (via Alpaca WebSocket)
- 📋 Watchlist with live price updates
- 💼 Portfolio & positions tracker
- 🛒 Order management (market, limit, stop orders)
- 🔁 Backtesting engine (run strategies on historical OHLCV data)
- 🪟 Flexible dockable / floatable panel layout (GIMP-style)

## Architecture

Goldeneye follows the **MVVM** (Model-View-ViewModel) pattern:

```
goldeneye/
├── core/          # Config, event bus, logging, exceptions
├── models/        # Pure data classes (Quote, Order, Position, …)
├── services/      # Business logic & external integrations
│   ├── broker/    # Alpaca broker adapter (abstract base + impl)
│   ├── data/      # Market data feed & historical loader
│   └── backtest/  # Backtesting engine & report generator
├── viewmodels/    # Qt-aware state; exposes signals to views
└── views/         # PyQt6 widgets, panels, main window
```

## Setup

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- An [Alpaca](https://alpaca.markets/) account (paper trading is free)

### Install

```bash
git clone https://github.com/Benjamin-Friess/Goldeneye.git
cd Goldeneye
poetry install
cp .env.example .env
# Edit .env with your Alpaca API keys
```

### Run

```bash
poetry run goldeneye
```

### Tests

```bash
poetry run pytest
```

### Lint / type-check

```bash
poetry run ruff check .
poetry run mypy goldeneye
```

## License

MIT
