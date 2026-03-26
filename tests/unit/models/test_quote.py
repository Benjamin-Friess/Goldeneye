from datetime import datetime

from goldeneye.models.quote import Quote


def test_quote_mid_price():
    q = Quote(symbol="AAPL", bid=149.0, ask=151.0, bid_size=100, ask_size=100)
    assert q.mid == 150.0


def test_quote_spread():
    q = Quote(symbol="AAPL", bid=149.0, ask=151.0, bid_size=100, ask_size=100)
    assert q.spread == 2.0
