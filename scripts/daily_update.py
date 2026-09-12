"""Headless daily refresh — cron-able, no broker required.

Refreshes the price cache, runs integrity checks on the fresh tail,
and appends a one-line status to research/daily-log.md. Exit code is
nonzero if integrity checks flag anything new, so a cron wrapper (or
`claude -p`) can escalate.

Usage: uv run python scripts/daily_update.py
Cron example (weekdays 18:30, after close):
  30 18 * * 1-5 cd /Users/Rishi/algo-proj && uv run python scripts/daily_update.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.analysis.benchmarks import equal_weight_returns
from src.analysis.returns import simple_returns
from src.analysis.stats import summary_stats
from src.data.fetch import fetch_prices, load_universe, universe_tickers
from src.data.integrity import run_report

LOG = Path(__file__).resolve().parents[1] / "research" / "daily-log.md"
RECENT_DAYS = 10  # integrity window: only flag problems in fresh data


def main() -> int:
    universe = load_universe()
    tickers = universe_tickers(include_benchmarks=True)
    panel = fetch_prices(tickers)  # extends cache to the latest close
    closes = panel["Close"]

    recent = panel.loc[panel.index[-RECENT_DAYS]:]
    report = run_report(recent, universe)
    flags = []
    if not report["bad_prices"].empty:
        flags.append(f"bad prices: {len(report['bad_prices'])}")
    if not report["long_gaps"].empty:
        flags.append(f"gaps: {len(report['long_gaps'])}")
    if not report["suspicious_moves"].empty:
        moves = report["suspicious_moves"]
        flags.append("moves>50%: " + ", ".join(
            f"{row['ticker']} {row['return']:+.0%}" for _, row in moves.iterrows()))

    uni = closes[universe_tickers()]
    ytd_start = closes.index[closes.index.year == closes.index[-1].year][0]
    ew = equal_weight_returns(uni, universe).loc[ytd_start:]
    spy = simple_returns(closes["SPY"]).loc[ytd_start:]
    ew_stats, spy_stats = summary_stats(ew), summary_stats(spy)

    line = (f"| {date.today().isoformat()} | {closes.index[-1].date()} "
            f"| {spy_stats['cagr']:.1%} | {ew_stats['cagr']:.1%} "
            f"| {'; '.join(flags) if flags else 'clean'} |")
    if not LOG.exists():
        LOG.write_text(
            "# Daily data log\n\n"
            "| run date | last bar | SPY YTD (ann.) | EW universe YTD (ann.) | integrity |\n"
            "|---|---|---|---|---|\n")
    with LOG.open("a") as f:
        f.write(line + "\n")
    print(line)
    return 1 if flags else 0


if __name__ == "__main__":
    raise SystemExit(main())
