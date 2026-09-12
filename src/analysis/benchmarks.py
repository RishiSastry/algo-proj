"""Benchmark (b): equal-weight, monthly-rebalanced basket of the universe.

Survivorship rule (CLAUDE.md #4): a ticker enters only after
ipo_date + 60 trading days. Data before ipo_date (predecessor entities,
SPAC shells) is masked out entirely.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SEASONING_DAYS = 60


def masked_closes(closes: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    """NaN out all bars before each ticker's ipo_date."""
    out = closes.copy()
    for t in out.columns:
        if t in universe.index and pd.notna(universe.loc[t, "ipo_date"]):
            out.loc[out.index < universe.loc[t, "ipo_date"], t] = np.nan
    return out


def eligibility(closes: pd.DataFrame, universe: pd.DataFrame,
                seasoning_days: int = SEASONING_DAYS) -> pd.DataFrame:
    """Boolean dates × tickers mask: True once a ticker has traded
    `seasoning_days` trading days beyond its ipo_date."""
    masked = masked_closes(closes, universe)
    elig = pd.DataFrame(False, index=closes.index, columns=closes.columns)
    for t in closes.columns:
        first = masked[t].first_valid_index()
        if first is None:
            continue
        pos = closes.index.get_loc(first) + seasoning_days
        if pos < len(closes.index):
            elig.loc[closes.index[pos]:, t] = True
    return elig


def equal_weight_returns(closes: pd.DataFrame, universe: pd.DataFrame,
                         seasoning_days: int = SEASONING_DAYS) -> pd.Series:
    """Daily simple returns of the equal-weight basket.

    Rebalanced at each month-end to 1/N across tickers eligible on that
    date; weights drift with prices within the month. No costs — this is
    a benchmark, held to the same standard as buy-and-hold SPY.
    """
    masked = masked_closes(closes, universe)
    elig = eligibility(closes, universe, seasoning_days)

    month = closes.index.to_period("M")
    rebalance_dates = closes.index.to_series().groupby(month).last()

    port_rets = []
    for i in range(len(rebalance_dates) - 1):
        t0, t1 = rebalance_dates.iloc[i], rebalance_dates.iloc[i + 1]
        members = [t for t in closes.columns
                   if elig.loc[t0, t] and pd.notna(masked.loc[t0, t])]
        window = masked.loc[t0:t1, members]
        if not members:
            idx = window.index[1:]
            port_rets.append(pd.Series(0.0, index=idx))
            continue
        growth = window / window.loc[t0]
        value = growth.mean(axis=1)  # equal weight at t0, drifting after
        port_rets.append(value.pct_change().iloc[1:])

    return pd.concat(port_rets).rename("EW_UNIVERSE")
