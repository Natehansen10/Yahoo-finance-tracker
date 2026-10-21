"""Run with: python -m tracker   (--once for a snapshot, --report for the daily email)"""

import argparse
import time
from datetime import date, datetime

from . import config, mailer
from .portfolio import load_holdings
from .prices import fetch_close_on, fetch_quotes
from .report import build_positions, daily_subject, latest_date, render, render_daily


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio watch from Yahoo Finance data.")
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    parser.add_argument("--report", action="store_true", help="print the daily report and email it")
    parser.add_argument("--force", action="store_true", help="with --report: email even if the market was closed today")
    args = parser.parse_args()

    holdings = load_holdings(config.HOLDINGS_FILE)
    held = sorted({h.symbol for h in holdings if h.symbol != config.CASH_SYMBOL})
    to_estimate = sorted({h.symbol for h in holdings if h.shares is None and h.symbol != config.CASH_SYMBOL})
    symbols = sorted(set(held) | set(config.WATCHLIST))

    # Estimated share counts never change, so fetch those closes once.
    snapshot_closes = fetch_close_on(to_estimate, config.SNAPSHOT_DATE)

    if args.report:
        quotes = fetch_quotes(symbols)
        positions = build_positions(holdings, quotes, snapshot_closes, config.CASH_SYMBOL)
        body = render_daily(positions, config.REPORT_TOP_N)
        print(body)
        as_of = latest_date(positions)
        if as_of != date.today() and not args.force:
            print(f"\nNot emailed: latest prices are from {as_of}, not today (market closed). Use --force to send anyway.")
            return
        subject = daily_subject(positions)
        env = mailer.load_env(config.ENV_FILE)
        print("\nEmailed." if mailer.send(subject, body, env) else "\nNot emailed: set up .env first (see .env.example).")
        return

    while True:
        quotes = fetch_quotes(symbols)
        positions = build_positions(holdings, quotes, snapshot_closes, config.CASH_SYMBOL)
        output = render(positions, quotes, config.WATCHLIST, config.TOP_N)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if args.once:
            print(f"Portfolio watch  {stamp}\n{output}")
            return
        print("\033[2J\033[H", end="")  # clear screen
        print(f"Portfolio watch  {stamp}  (refresh {config.REFRESH_SECONDS}s, Ctrl+C to quit)\n{output}")
        try:
            time.sleep(config.REFRESH_SECONDS)
        except KeyboardInterrupt:
            return


if __name__ == "__main__":
    main()
