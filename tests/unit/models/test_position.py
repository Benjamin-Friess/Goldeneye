from goldeneye.models.position import Position


def test_position_market_value():
    pos = Position(symbol="AAPL", qty=10, avg_entry_price=100.0, current_price=120.0)
    assert pos.market_value == 1200.0


def test_position_unrealized_pnl():
    pos = Position(symbol="AAPL", qty=10, avg_entry_price=100.0, current_price=120.0)
    assert pos.unrealized_pnl == 200.0


def test_position_unrealized_pnl_pct():
    pos = Position(symbol="AAPL", qty=10, avg_entry_price=100.0, current_price=120.0)
    assert abs(pos.unrealized_pnl_pct - 0.2) < 1e-9
