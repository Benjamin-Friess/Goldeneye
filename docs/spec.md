# Goldeneye – Technical Specification

## 1. Overview

**Goldeneye** is a desktop stock-trading application for active traders.  
It runs natively on Linux, macOS, and Windows, is written in Python 3.11+,
and uses PyQt6 for its graphical interface.

---

## 2. Goals & Non-Goals

### Goals
- Real-time Level-1 quotes and minute bars (via Alpaca WebSocket)
- Candlestick chart with zoom / pan
- Portfolio and position tracker (equity, unrealized P&L)
- Order management: market, limit, and stop orders (via Alpaca REST)
- Event-driven backtesting engine for custom strategies
- **Top 100 stocks panel** with multi-select and price-evolution chart (1D → 1Y)
- Dockable, floatable, re-arrangeable panels (persisted across sessions)
- Pluggable broker interface (swap Alpaca for IBKR, etc.)

### Non-Goals (v1)
- Level-2 order book / depth of market
- Options chains
- Multi-account support
- Mobile / web interface

---

## 3. Architecture

Goldeneye follows **MVVM** (Model – View – ViewModel).

```
┌──────────────────────────────────────────────┐
│  Views  (PyQt6 widgets, QDockWidget panels)  │
│  Receive data via Qt signals from ViewModels │
└───────────────────┬──────────────────────────┘
                    │ Qt signals / slots
┌───────────────────▼──────────────────────────┐
│  ViewModels  (QObject subclasses)            │
│  Manage UI state; call Services; emit signals│
└───────────────────┬──────────────────────────┘
                    │ async calls / direct calls
┌───────────────────▼──────────────────────────┐
│  Services  (broker, data feed, backtester)   │
│  Pure business logic; no Qt dependency       │
└───────────────────┬──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│  Models  (frozen dataclasses)                │
│  Quote, Bar, Order, Position, Portfolio, …   │
└──────────────────────────────────────────────┘
```

### 3.1 Event Bus

`goldeneye.core.events.EventBus` is a singleton `QObject` that exposes typed
Qt signals (`quote_received`, `bar_received`, `order_updated`, …).  
Components publish by calling `bus.<signal>.emit(payload)`.  
Components subscribe by connecting slots: `bus.<signal>.connect(handler)`.  
Because Qt queues cross-thread signal deliveries, the bus is thread-safe.

---

## 4. Module Reference

| Package | Responsibility |
|---|---|
| `goldeneye.core` | Config, logging, event bus, exceptions |
| `goldeneye.models` | Domain data classes (immutable where possible) |
| `goldeneye.services.broker` | Abstract `BrokerBase` + `AlpacaBroker` adapter |
| `goldeneye.services.data` | `DataFeed` (WebSocket) + `HistoricalDataLoader` (REST) + `SP100` symbol list |
| `goldeneye.services.backtest` | `BacktestEngine` + `BacktestResult` |
| `goldeneye.viewmodels` | Qt-aware state for each panel |
| `goldeneye.views` | `MainWindow`, dockable panels, custom widgets |

---

## 5. UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  Menu bar                                               │
├──────────┬──────────────────────────────┬───────────────┤
│Top 100   │                              │  Portfolio    │
│Stocks    │    Chart  (central widget)   │  (dock)       │
│ (dock)   │                              ├───────────────┤
├──────────┤                              │  Backtest     │
│Watchlist │                              │  (dock)       │
│ (dock)   │                              │               │
├──────────┴──────────────────────────────┴───────────────┤
│  Orders  (bottom dock)                                  │
├─────────────────────────────────────────────────────────┤
│  Status bar                                             │
└─────────────────────────────────────────────────────────┘
```

Selecting symbols in the Top 100 panel and clicking **Show Chart** opens a
separate floating `MultiChartWindow` with a normalised % change plot.

### Top 100 Stocks Panel

- Searchable / filterable table of 100 S&P 100 constituents (symbol + company name)
- Multi-select (Ctrl+click / Shift+click) for up to 10 symbols
- Time-range selector: **1D** (5-min bars) · **5D** (1-h bars) · **1M / 3M / 6M / 1Y** (daily bars)
- "Show Chart" button opens / updates the floating `MultiChartWindow`

### Multi-Symbol Chart Window

- Floating `QDialog` (independent window, stays on top)
- Lines normalised to **% change from period start** so all symbols can be compared on one scale
- Up to 10 coloured lines with auto-legend
- Fetches data in a background thread (non-blocking UI)
- **Movable** – drag title bar to re-position
- **Floatable** – double-click or drag out to become a standalone window
- **Closable** – re-open from View menu
- **Tabifiable** – drop one dock onto another to create tabs

Panel positions are persisted via `QSettings` between sessions.

---

## 6. Data Flow

### 6.1 Live quote

```
Alpaca WebSocket → DataFeed._on_quote()
  → bus.quote_received.emit(Quote)
    → WatchlistPanel (update price column)
```

### 6.2 Place order

```
User clicks "Place Order" in OrderPanel
  → OrdersViewModel.place_order(...)
    → AlpacaBroker.place_order(...)  [async]
      → bus.order_updated.emit(Order)
        → OrderPanel._refresh_table()
```

### 6.3 Backtest

```
User clicks "Run Backtest" in BacktestPanel
  → BacktestViewModel.run(strategy, fn, bars)
    → BacktestEngine.run()  [background thread]
      → BacktestViewModel.progress_updated.emit(%)
      → BacktestViewModel.result_ready.emit(BacktestResult)
        → BacktestPanel._show_result()
```

---

## 7. Broker Abstraction

New brokers implement `goldeneye.services.broker.base.BrokerBase`:

```python
class MyBroker(BrokerBase):
    async def connect(self) -> None: ...
    async def place_order(self, ...) -> Order: ...
    # ... etc.
```

Swap the broker in `MainViewModel.__init__` or inject via config.

---

## 8. Strategy API (Backtesting)

A strategy is a callable with signature:

```python
def my_strategy(bar: Bar, portfolio: Portfolio) -> list[Order]:
    ...
```

For stateful strategies, use a class with `__call__`:

```python
class MACrossover:
    def __init__(self, fast: int = 10, slow: int = 50): ...
    def __call__(self, bar: Bar, portfolio: Portfolio) -> list[Order]: ...
```

Pass the instance as `strategy_fn` to `BacktestViewModel.run()`.

---

## 9. Configuration

All settings are loaded from `.env` (or environment variables):

| Variable | Default | Description |
|---|---|---|
| `ALPACA_API_KEY` | – | Alpaca API key |
| `ALPACA_SECRET_KEY` | – | Alpaca secret key |
| `ALPACA_PAPER` | `true` | Paper vs live trading |
| `LOG_LEVEL` | `INFO` | Loguru log level |
| `DB_URL` | `sqlite+aiosqlite:///goldeneye.db` | SQLAlchemy DB URL |

---

## 10. Technology Stack

| Concern | Library | Version |
|---|---|---|
| GUI | PyQt6 | ≥ 6.6 |
| Charting | pyqtgraph | ≥ 0.13 |
| Broker API | alpaca-py | latest |
| Data frames | pandas | ≥ 2.0 |
| Numerics | numpy | ≥ 1.26 |
| Config | pydantic-settings | ≥ 2.0 |
| Logging | loguru | ≥ 0.7 |
| DB (future) | SQLAlchemy + aiosqlite | ≥ 2.0 |
| HTTP | httpx | ≥ 0.27 |
| Package mgmt | Poetry | ≥ 1.8 |
| Linting | ruff | latest |
| Type checking | mypy (strict) | ≥ 1.0 |
| Testing | pytest + pytest-qt | latest |

---

## 11. Testing Strategy

| Layer | Tool | Coverage target |
|---|---|---|
| Models | pytest | 100 % |
| Services (non-network) | pytest | ≥ 80 % |
| ViewModels | pytest-qt | ≥ 70 % |
| Views | pytest-qt | smoke tests |
| Broker / DataFeed | integration tests (mocked) | key paths |

Run tests: `poetry run pytest --cov=goldeneye`

---

## 12. Future Work

- Candlestick renderer (replace line chart in `ChartPanel`)
- Technical indicators overlay (SMA, EMA, RSI, MACD)
- Strategy editor (write Python in-app)
- Alert system (price threshold, order fills)
- Multi-broker support (Interactive Brokers via TWS API)
- Historical data caching (SQLite)
- Dark / light theme toggle
