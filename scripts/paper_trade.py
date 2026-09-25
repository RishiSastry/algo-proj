"""Daily paper-trading run — the trend sleeve in two implementations.

Accounts under paper/:
- basket/    fractional shares, the strategy-faithful EW basket (what the
             research validated; not tradable at Schwab with $1K).
- smh/       whole shares of SMH only (simplest Schwab-implementable proxy).
- slices16/  the S&P-500-member sub-basket, fractional via Schwab Stock
             Slices (passed its pre-registered test 2026-09-13; membership
             must be re-verified before live use). Own trend gate on its
             own 16-name index.

Each run refreshes prices, then processes every trading day since the
account's last run (safe to miss days; idempotent per day). Targets
decided at close t fill at the open of t+1 via the simulator.

Usage: uv run python scripts/paper_trade.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import pandas as pd

from src.data.fetch import fetch_prices, load_universe, universe_tickers
from src.paper.simulator import Account
from src.strategies.basket_timing import MA_WINDOW, basket_index, generate_weights_trend

PAPER_DIR = REPO / "paper"

# S&P 500 members of the universe (checked 2026-09-13; re-verify for live)
SLICES16 = ["MSFT", "AMZN", "GOOGL", "META", "ORCL", "NVDA", "AMD", "AVGO",
            "MU", "MRVL", "QCOM", "INTC", "DELL", "ANET", "SMCI", "VRT"]


def main() -> int:
    universe = load_universe()
    tickers = universe_tickers()
    panel = fetch_prices(tickers + ["SPY", "SMH"])
    uni_closes = panel["Close"][tickers]

    basket_weights = generate_weights_trend(uni_closes, universe)
    slices_weights = generate_weights_trend(uni_closes[SLICES16], universe)
    idx = basket_index(uni_closes, universe)
    signal = (idx > idx.rolling(MA_WINDOW).mean()).astype(float)

    # NAV marks tolerate a vendor NaN via last known close; fills use raw
    # opens so the simulator defers instead of filling at a stale price
    open_panel = panel["Open"]
    close_panel = panel["Close"].ffill()

    accounts = [
        ("basket", Account.load(PAPER_DIR / "basket", whole_shares=False),
         basket_weights),
        ("smh", Account.load(PAPER_DIR / "smh", whole_shares=True), None),
        ("slices16", Account.load(PAPER_DIR / "slices16", whole_shares=False),
         slices_weights),
    ]

    for name, acct, weights in accounts:
        if acct.last_processed:
            todo = panel.index[panel.index > pd.Timestamp(acct.last_processed)]
        else:
            todo = panel.index[-1:]  # new account: start today, no replay

        for date in todo:
            if weights is not None:
                row = weights.loc[date]
                targets = {t: float(w) for t, w in row.items() if w > 0}
                opens = open_panel.loc[date]
                closes = close_panel.loc[date]
            else:
                targets = {"SMH": 1.0} if signal.loc[date] > 0 else {}
                opens = open_panel.loc[date][["SMH"]]
                closes = close_panel.loc[date][["SMH"]]
            acct.process_day(date, opens, closes, targets)

        nav = acct.nav(close_panel.iloc[-1])
        state = "IN (uptrend)" if signal.iloc[-1] > 0 else "OUT (cash)"
        print(f"{name:8s} NAV ${nav:,.2f} | signal {state} | "
              f"positions {len(acct.positions)} | last {acct.last_processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
