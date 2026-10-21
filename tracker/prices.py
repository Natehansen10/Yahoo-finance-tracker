"""Price fetching. The only module that talks to Yahoo."""

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
import yfinance as yf


@dataclass
class Quote:
    price: float
    prev_close: float
    as_of: date | None = None  # trading day of the latest price

    @property
    def change(self) -> float:
        return self.price - self.prev_close

    @property
    def change_pct(self) -> float:
        return self.change / self.prev_close * 100 if self.prev_close else 0.0


def _closes(symbols: list[str], **kwargs) -> pd.DataFrame:
    data = yf.download(symbols, progress=False, auto_adjust=False, threads=True, **kwargs)
    if data.empty:
        return pd.DataFrame()
    closes = data["Close"]
    if isinstance(closes, pd.Series):
        closes = closes.to_frame(symbols[0])
    return closes


def fetch_quotes(symbols: list[str]) -> dict[str, Quote]:
    """Latest price and previous close per symbol. Missing symbols are left out."""
    if not symbols:
        return {}
    closes = _closes(symbols, period="5d")
    quotes = {}
    for sym in closes.columns:
        series = closes[sym].dropna()
        if len(series) >= 2:
            quotes[sym] = Quote(float(series.iloc[-1]), float(series.iloc[-2]), series.index[-1].date())
        elif len(series) == 1:
            quotes[sym] = Quote(float(series.iloc[-1]), float(series.iloc[-1]), series.index[-1].date())
    return quotes


def fetch_close_on(symbols: list[str], day: str) -> dict[str, float]:
    """Closing price per symbol on one trading day."""
    if not symbols:
        return {}
    start = date.fromisoformat(day)
    closes = _closes(symbols, start=start.isoformat(), end=(start + timedelta(days=1)).isoformat())
    return {sym: float(closes[sym].dropna().iloc[-1]) for sym in closes.columns if not closes[sym].dropna().empty}
