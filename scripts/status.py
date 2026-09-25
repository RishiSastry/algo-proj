"""Regenerate STATUS.md — the at-a-glance state of the whole system.

Runs nightly at the end of the cron chain; safe to run any time.
Reads only local state (cache, ledgers, logs) — no network.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import pandas as pd

from src.analysis.returns import equity_curve, simple_returns
from src.data.fetch import load_universe, universe_tickers
from src.data import cache
from src.strategies.basket_timing import MA_WINDOW, basket_index

BOOKS = ["basket", "slices16", "smh"]
INCEPTION = "2026-09-15"  # first paper fills


def nav_series(book: str) -> pd.Series:
    ledger = pd.read_csv(REPO / "paper" / book / "ledger.csv")
    marks = ledger[ledger["event"] == "MARK"].dropna(subset=["value"])
    s = pd.Series(marks["value"].to_numpy(), index=pd.to_datetime(marks["date"]))
    return s[~s.index.duplicated(keep="last")]


def main() -> int:
    universe = load_universe()
    closes = pd.DataFrame({t: cache.load(t)["Close"]
                           for t in universe_tickers(include_benchmarks=True)})
    uni_closes = closes[universe_tickers()]

    idx = basket_index(uni_closes, universe)
    ma = idx.rolling(MA_WINDOW).mean()
    in_trend = bool(idx.iloc[-1] > ma.iloc[-1])
    margin = idx.iloc[-1] / ma.iloc[-1] - 1
    state = (idx > ma).astype(int)
    last_flip = state.index[state.diff().ne(0) & state.index.to_series().notna()][-1]

    lines = [
        "# STATUS — AI-infra systematic trading",
        "",
        f"*Auto-generated {date.today().isoformat()} by `scripts/status.py` "
        f"(nightly via cron). Last price bar: {closes.index[-1].date()}.*",
        "",
        "## Signal",
        "",
        f"**{'IN — uptrend' if in_trend else 'OUT — cash'}** · basket index is "
        f"{margin:+.1%} vs its {MA_WINDOW}d MA · state unchanged since "
        f"{last_flip.date()}.",
        "",
        "The strategy: hold the equal-weight basket while its index is above "
        "the 210-day MA (month-end check, next-day execution); cash otherwise.",
        "",
        "## Paper books (started 2026-09-15, $1K each)",
        "",
        "| book | holds | NAV | total return |",
        "|---|---|---|---|",
    ]

    navs = {}
    for book in BOOKS:
        try:
            navs[book] = nav_series(book)
        except FileNotFoundError:
            continue
    desc = {"basket": "27 names, fractional (ideal)",
            "slices16": "16 S&P names via Stock Slices (Phase-1 candidate)",
            "smh": "1 whole-share ETF (fallback)"}
    for book, s in sorted(navs.items(), key=lambda kv: -kv[1].iloc[-1]):
        lines.append(f"| {book} | {desc[book]} | ${s.iloc[-1]:,.2f} | "
                     f"{s.iloc[-1]/1000 - 1:+.1%} |")

    bench = []
    for b in ["SPY", "SMH"]:
        r = simple_returns(closes[b]).loc[INCEPTION:]
        bench.append(f"{b} buy&hold {float(equity_curve(r).iloc[-1]) - 1:+.1%}")
    lines += ["", f"Benchmarks since inception: {', '.join(bench)}.", ""]

    log = (REPO / "research" / "daily-log.md").read_text().strip().splitlines()
    lines += ["## Ops", "",
              f"Last daily-log entry: `{log[-1]}`",
              "",
              "- Cron: weekdays 18:30 — data refresh, integrity, paper trade, status.",
              "- Missed runs self-heal via catch-up; integrity flags missing bars.",
              "- Incidents: see `research/2026-09-24-data-incident.md` (resolved).",
              "",
              "## Pending decisions (Rishi)",
              "",
              "- AMZN in or out of the tradable sleeve (48% locked exposure at MS).",
              "- Phase-1 go/no-go: after ~4+ weeks of paper, if books track "
              "expectations → $1K live in Schwab via Stock Slices (slices16).",
              "- Phase-2 gate (months out): sizing, hedge-vs-sleeve use of the "
              "signal, sector diversification, options overlay.",
              ""]

    (REPO / "STATUS.md").write_text("\n".join(lines))
    print(f"STATUS.md updated: signal {'IN' if in_trend else 'OUT'} "
          f"({margin:+.1%}), books: " +
          ", ".join(f"{b} ${s.iloc[-1]:,.0f}" for b, s in navs.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
