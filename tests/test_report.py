"""Offline tests. No Yahoo calls."""

from pathlib import Path

from tracker.portfolio import load_holdings, to_yahoo
from tracker.prices import Quote
from tracker.report import build_positions, render

EXAMPLE = Path(__file__).resolve().parent.parent / "holdings.example.csv"


def test_to_yahoo():
    assert to_yahoo("brk.b") == "BRK-B"


def test_example_loads():
    holdings = load_holdings(EXAMPLE)
    assert [h.symbol for h in holdings] == ["AAPL", "BRK-B", "CASH", "VTI"]
    assert holdings[3].shares is None and holdings[3].value == 5000.0


def test_positions_and_totals():
    holdings = load_holdings(EXAMPLE)
    quotes = {"AAPL": Quote(200.0, 190.0), "BRK-B": Quote(500.0, 500.0), "VTI": Quote(260.0, 250.0)}
    positions = build_positions(holdings, quotes, {"VTI": 250.0}, "CASH")
    by_sym = {p.symbol: p for p in positions}

    assert by_sym["VTI"].estimated and by_sym["VTI"].shares == 20.0
    assert by_sym["VTI"].value == 5200.0
    assert by_sym["CASH"].value == 250.0
    assert by_sym["AAPL"].day_change == 100.0

    out = render(positions, quotes, ["AAPL", "ZZZZ"], top_n=10)
    # 2000 + 1250 + 250 + 5200
    assert "TOTAL  $8,700.00" in out
    assert "ZZZZ" in out and "no price" in out


def test_missing_price_left_out():
    holdings = load_holdings(EXAMPLE)
    positions = build_positions(holdings, {}, {}, "CASH")
    out = render(positions, {}, [], top_n=10)
    assert "TOTAL  $250.00" in out
    assert "No price" in out


def test_cash_has_no_gain():
    holdings = load_holdings(EXAMPLE)
    positions = build_positions(holdings, {}, {}, "CASH")
    cash = next(p for p in positions if p.symbol == "CASH")
    assert cash.cost_basis is None


def test_estimate_note_only_when_estimated():
    holdings = [h for h in load_holdings(EXAMPLE) if h.shares is not None]
    quotes = {"AAPL": Quote(200.0, 190.0), "BRK-B": Quote(500.0, 500.0)}
    exact = render(build_positions(holdings, quotes, {}, "CASH"), quotes, [], top_n=10)
    assert "estimated" not in exact

    holdings = load_holdings(EXAMPLE)
    quotes["VTI"] = Quote(260.0, 250.0)
    estimated = render(build_positions(holdings, quotes, {"VTI": 250.0}, "CASH"), quotes, [], top_n=10)
    assert "estimated" in estimated
