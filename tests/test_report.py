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


def _daily_positions():
    from datetime import date
    holdings = load_holdings(EXAMPLE)
    d = date(2026, 10, 20)
    quotes = {
        "AAPL": Quote(200.0, 190.0, d),   # 10 sh: +$100
        "BRK-B": Quote(480.0, 500.0, d),  # 2.5 sh: -$50
        "VTI": Quote(260.0, 250.0, d),    # 20 sh est: +$200
    }
    return build_positions(holdings, quotes, {"VTI": 250.0}, "CASH")


def test_daily_report():
    from tracker.report import daily_subject, render_daily, totals
    positions = _daily_positions()
    value, day, _ = totals(positions)
    assert day == 250.0
    out = render_daily(positions, top_n=5)
    assert "close of Tue Oct 20, 2026" in out
    assert "Brokerage" in out and "Robo Account" in out
    assert out.index("VTI") < out.index("AAPL")  # biggest gainer first
    assert "-$50.00" in out.split("Top losers")[1]
    assert daily_subject(positions) == "Portfolio Oct 20: +$250.00 (+2.98%)"


def test_mailer(monkeypatch, tmp_path):
    from tracker import mailer

    env_file = tmp_path / ".env"
    env_file.write_text("# note\nTRACKER_EMAIL_USER=me@example.com\nTRACKER_EMAIL_PASSWORD=abcd efgh\n")
    env = mailer.load_env(env_file)
    assert env["TRACKER_EMAIL_USER"] == "me@example.com"

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent["server"] = (host, port)
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def login(self, user, password): sent["login"] = (user, password)
        def send_message(self, msg): sent["msg"] = msg

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    assert mailer.send("Subject", "Body", env) is True
    assert sent["server"] == ("smtp.gmail.com", 465)
    assert sent["login"] == ("me@example.com", "abcdefgh")  # spaces stripped
    assert sent["msg"]["To"] == "me@example.com" and sent["msg"]["Subject"] == "Subject"


def test_mailer_not_configured():
    from tracker import mailer
    assert mailer.send("s", "b", {}) is False
