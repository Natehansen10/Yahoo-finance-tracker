"""Turn holdings and quotes into text tables. No network calls here."""

from collections import defaultdict
from dataclasses import dataclass

from .portfolio import Holding
from .prices import Quote


@dataclass
class Position:
    account: str
    symbol: str
    shares: float
    estimated: bool
    cost_basis: float | None
    quote: Quote | None

    @property
    def value(self) -> float:
        return self.shares * self.quote.price if self.quote else 0.0

    @property
    def day_change(self) -> float:
        return self.shares * self.quote.change if self.quote else 0.0


def build_positions(
    holdings: list[Holding],
    quotes: dict[str, Quote],
    snapshot_closes: dict[str, float],
    cash_symbol: str,
) -> list[Position]:
    positions = []
    for h in holdings:
        quote = Quote(1.0, 1.0) if h.symbol == cash_symbol else quotes.get(h.symbol)
        shares, estimated = h.shares, False
        if shares is None:
            close = 1.0 if h.symbol == cash_symbol else snapshot_closes.get(h.symbol)
            shares, estimated = (h.value / close, True) if close else (0.0, True)
        cost_basis = None if h.symbol == cash_symbol else h.cost_basis  # cash has no gain
        positions.append(Position(h.account, h.symbol, shares, estimated, cost_basis, quote))
    return positions


def _money(x: float) -> str:
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def _signed(x: float) -> str:
    return f"+{_money(x)}" if x >= 0 else _money(x)


def _pct(x: float) -> str:
    return f"{x:+.2f}%"


def render(positions: list[Position], watch: dict[str, Quote], watchlist: list[str], top_n: int) -> str:
    lines = []
    by_account = defaultdict(list)
    for p in positions:
        by_account[p.account].append(p)

    grand_value = grand_day = 0.0
    missing = []
    for account, rows in by_account.items():
        rows.sort(key=lambda p: p.value, reverse=True)
        value = sum(p.value for p in rows)
        day = sum(p.day_change for p in rows)
        prev = value - day
        grand_value += value
        grand_day += day
        missing += [f"{p.account}: {p.symbol}" for p in rows if p.quote is None]

        lines.append(f"\n{account}  {_money(value)}  {_signed(day)} ({_pct(day / prev * 100 if prev else 0)}) today")
        lines.append(f"  {'SYMBOL':<7}{'SHARES':>11}{'PRICE':>11}{'DAY':>9}{'VALUE':>13}{'GAIN':>12}")
        for p in rows[:top_n]:
            if p.quote is None:
                lines.append(f"  {p.symbol:<7}{'no price':>11}")
                continue
            shares = f"{p.shares:,.4f}" + ("~" if p.estimated else " ")
            gain = _signed(p.value - p.cost_basis) if p.cost_basis is not None else ""
            lines.append(
                f"  {p.symbol:<7}{shares:>11}{_money(p.quote.price):>11}"
                f"{_pct(p.quote.change_pct):>9}{_money(p.value):>13}{gain:>12}"
            )
        if len(rows) > top_n:
            lines.append(f"  ... and {len(rows) - top_n} more")

    prev = grand_value - grand_day
    lines.append(f"\nTOTAL  {_money(grand_value)}  {_signed(grand_day)} ({_pct(grand_day / prev * 100 if prev else 0)}) today")

    lines.append("\nWatchlist")
    for sym in watchlist:
        q = watch.get(sym)
        lines.append(f"  {sym:<7}{_money(q.price):>11}{_pct(q.change_pct):>9}" if q else f"  {sym:<7}{'no price':>11}")

    if any(p.estimated for p in positions):
        lines.append("\n~ shares estimated from a dollar value.")
    lines.append("\nPrices from Yahoo, may be delayed.")
    if missing:
        lines.append("No price (left out of totals): " + ", ".join(missing))
    return "\n".join(lines)


def totals(positions: list[Position]) -> tuple[float, float, float]:
    """Total value, day change in dollars, and day change in percent."""
    value = sum(p.value for p in positions)
    day = sum(p.day_change for p in positions)
    prev = value - day
    return value, day, (day / prev * 100 if prev else 0.0)


def latest_date(positions: list[Position]):
    """Newest trading day among the prices, or None if nothing priced."""
    dates = [p.quote.as_of for p in positions if p.quote and p.quote.as_of]
    return max(dates) if dates else None


def daily_subject(positions: list[Position]) -> str:
    """Email subject: date and the day's change, readable without opening the email."""
    _, day, pct = totals(positions)
    as_of = latest_date(positions)
    return f"Portfolio {as_of:%b %d}: {_signed(day)} ({_pct(pct)})"


def render_daily(positions: list[Position], top_n: int = 5) -> str:
    """Short end-of-day summary: total, each account, biggest movers."""
    as_of = latest_date(positions)
    value, day, pct = totals(positions)
    lines = [f"Daily report, close of {as_of:%a %b %d, %Y}" if as_of else "Daily report"]
    lines.append(f"TOTAL  {_money(value)}  {_signed(day)} ({_pct(pct)})")

    by_account = defaultdict(list)
    for p in positions:
        by_account[p.account].append(p)
    lines.append("\nBy account")
    for account, rows in sorted(by_account.items(), key=lambda kv: -totals(kv[1])[0]):
        v, d, c = totals(rows)
        lines.append(f"  {account:<20}{_money(v):>13}{_signed(d):>11}{_pct(c):>9}")

    # Same ticker can sit in several accounts, so combine by symbol.
    movers = defaultdict(float)
    pcts = {}
    for p in positions:
        if p.quote and p.quote.as_of:
            movers[p.symbol] += p.day_change
            pcts[p.symbol] = p.quote.change_pct
    ranked = sorted(movers.items(), key=lambda kv: kv[1], reverse=True)
    gainers = [kv for kv in ranked if kv[1] > 0][:top_n]
    losers = [kv for kv in reversed(ranked) if kv[1] < 0][:top_n]
    for title, rows in (("Top gainers", gainers), ("Top losers", losers)):
        lines.append(f"\n{title} (dollars, all accounts)")
        lines += [f"  {sym:<7}{_signed(amt):>11}{_pct(pcts[sym]):>9}" for sym, amt in rows] or ["  none"]

    missing = sorted({p.symbol for p in positions if p.quote is None})
    if missing:
        lines.append("\nNo price (left out): " + ", ".join(missing))
    return "\n".join(lines)
