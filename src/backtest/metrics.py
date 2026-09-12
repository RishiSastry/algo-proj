"""Backtest metrics: summary stats plus benchmark comparison.

Every strategy is reported against (a) buy-and-hold SPY and (b) the
equal-weight universe basket (CLAUDE.md #5).
"""

from __future__ import annotations

import pandas as pd

from src.analysis.stats import summary_stats
from src.backtest.engine import BacktestResult


def hit_rate(returns: pd.Series) -> float:
    r = returns[returns != 0].dropna()
    return float((r > 0).mean()) if len(r) else float("nan")


def strategy_report(result: BacktestResult,
                    benchmarks: dict[str, pd.Series]) -> pd.DataFrame:
    """Stats table: strategy (net and gross) vs. each benchmark, all
    restricted to the strategy's live date range."""
    live = result.net_returns.loc[result.exposure.ne(0).cummax()]
    rows = {
        "strategy (net)": dict(summary_stats(live),
                               hit_rate=hit_rate(live),
                               ann_turnover=result.annual_turnover(),
                               avg_exposure=result.avg_exposure()),
        "strategy (gross)": summary_stats(result.gross_returns.loc[live.index]),
    }
    for name, bench in benchmarks.items():
        rows[name] = summary_stats(bench.loc[bench.index.intersection(live.index)])
    return pd.DataFrame(rows).T


def format_report(report: pd.DataFrame) -> pd.DataFrame:
    out = report.copy()
    pct = ["cagr", "ann_vol", "max_drawdown", "hit_rate", "avg_exposure"]
    two = ["sharpe", "sortino", "calmar", "ann_turnover"]
    for col in pct:
        if col in out:
            out[col] = out[col].map(lambda v: f"{v:.1%}" if pd.notna(v) else "—")
    for col in two:
        if col in out:
            out[col] = out[col].map(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
    return out
