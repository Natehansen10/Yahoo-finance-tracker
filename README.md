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

## Daily email report

`python -m tracker --report` prints an end-of-day summary and emails it: total, each account, and the top 5 gainers and losers in dollars. It skips the email when the market was closed that day (weekends, holidays). Add `--force` to send anyway.

Set up email once:

1. Turn on 2-Step Verification for your Google account, then create an app password at https://myaccount.google.com/apppasswords.
2. Copy `.env.example` to `.env` and fill in your address and the app password. `.env` is gitignored.
3. Test it: `python -m tracker --report --force`

Run it every weekday on Windows with Task Scheduler. The market closes at 4:00 PM Eastern, so set the time to about 4:35 PM Eastern in your local time (2:35 PM Mountain):

```
schtasks /create /tn "PortfolioReport" /sc weekly /d MON,TUE,WED,THU,FRI /st 14:35 /tr "C:\path\to\Yahoo-finance-tracker\run_report.bat"
```

The PC must be on and signed in at that time. Output goes to `report.log`.

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
