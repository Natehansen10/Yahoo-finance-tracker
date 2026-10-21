"""All tunable settings live here."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Your real holdings. Gitignored, never commit it. Copy holdings.example.csv to start.
HOLDINGS_FILE = ROOT / "holdings.csv"

# Seconds between refreshes in live mode.
REFRESH_SECONDS = 60

# Show only the largest N positions per account. The account total still counts all of them.
TOP_N = 15

# Rows with a dollar value but no share count get their shares estimated
# from the closing price on this date (the day the values were copied).
SNAPSHOT_DATE = "2026-10-15"

# Symbol for uninvested cash. Priced at $1, never fetched.
CASH_SYMBOL = "CASH"

# Tickers to watch without holding them.
WATCHLIST = [
    "DIS", "PLTR", "OKTA", "MSFT", "COST", "IBM", "AMZN",
    "META", "ARKF", "NET", "QQQ", "HOOD", "SMCI",
]
