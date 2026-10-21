"""Run with: python -m tracker   (add --once for a single snapshot)"""

import argparse
import time
from datetime import datetime

from . import config
from .portfolio import load_holdings
from .prices import fetch_close_on, fetch_quotes
from .report import build_positions, render


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio watch from Yahoo Finance data.")
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    args = parser.parse_args()

    holdings = load_holdings(config.HOLDINGS_FILE)
    held = sorted({h.symbol for h in holdings if h.symbol != config.CASH_SYMBOL})
    to_estimate = sorted({h.symbol for h in holdings if h.shares is None and h.symbol != config.CASH_SYMBOL})
    symbols = sorted(set(held) | set(config.WATCHLIST))

    # Estimated share counts never change, so fetch those closes once.
    snapshot_closes = fetch_close_on(to_estimate, config.SNAPSHOT_DATE)

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
