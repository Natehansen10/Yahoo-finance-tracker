# Yahoo-finance-tracker

A terminal portfolio watch. Pulls prices from Yahoo Finance with `yfinance` and shows each account's value, today's change, and gain, plus a watchlist. Refreshes every 60 seconds.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp holdings.example.csv holdings.csv   # then fill in your positions
```

## Run

```bash
python -m tracker          # live, refreshes every 60s
python -m tracker --once   # one snapshot
```

## holdings.csv

One row per position. `holdings.csv` is gitignored. Never commit it: this repo is public.

| column | meaning |
|---|---|
| `account` | Any label. Rows are grouped by it. |
| `symbol` | Ticker. `BRK.B` style is converted to Yahoo's `BRK-B`. Use `CASH` for cash (shares = dollars). |
| `shares` | Share count. Leave blank to estimate from `value`. |
| `cost_basis` | Total cost in dollars. Optional. Enables the GAIN column. |
| `value` | Dollar value on `SNAPSHOT_DATE`. Used only when `shares` is blank. |

Estimated share counts are marked `~`. Replace them with real share counts when you have them.

## Settings

All in `tracker/config.py`: refresh interval, top N rows per account, snapshot date, watchlist.

## Tests

```bash
pip install pytest
python -m pytest tests
```

Tests run offline with fake prices.

## Notes

- Yahoo has no official API. `yfinance` uses its internal endpoints, so it can break when Yahoo changes them. Upgrade with `pip install -U yfinance`.
- Personal use only, per Yahoo's terms.
