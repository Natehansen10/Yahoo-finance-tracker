"""Load holdings from CSV."""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Holding:
    account: str
    symbol: str
    shares: float | None  # None means estimate it from `value`
    cost_basis: float | None
    value: float | None  # dollar value on SNAPSHOT_DATE, used only when shares is missing


def _num(text: str) -> float | None:
    text = text.strip().replace("$", "").replace(",", "")
    return float(text) if text else None


def to_yahoo(symbol: str) -> str:
    """Brokers write class shares as BRK.B. Yahoo uses BRK-B."""
    return symbol.strip().upper().replace(".", "-")


def load_holdings(path: Path) -> list[Holding]:
    if not path.exists():
        raise SystemExit(f"No holdings file at {path}. Copy holdings.example.csv to holdings.csv.")
    holdings = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            h = Holding(
                account=row["account"].strip(),
                symbol=to_yahoo(row["symbol"]),
                shares=_num(row.get("shares", "")),
                cost_basis=_num(row.get("cost_basis", "")),
                value=_num(row.get("value", "")),
            )
            if h.shares is None and h.value is None:
                raise SystemExit(f"{h.account} {h.symbol}: needs shares or value.")
            holdings.append(h)
    return holdings
