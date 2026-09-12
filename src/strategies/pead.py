"""Post-earnings-announcement drift (PEAD) v0.

Rule (pre-registered, untuned):
- Event: a reported quarter with a positive EPS surprise
  (surprise_pct >= MIN_SURPRISE_PCT).
- Entry: signal is formed at the close of the first trading day AFTER
  the announcement date — one full day after the announcement,
  regardless of before/after-close timing. The engine adds one more
  day of execution lag on top (conservative: the day-one reaction gap
  is deliberately not traded).
- Hold: HOLD_DAYS trading days, truncated early by the ticker's next
  announcement (never hold through the next print on a stale signal).
- Sizing: equal weight across active events, capped at MAX_WEIGHT per
  name; remainder in cash.

Same eligibility rule as everything else: ipo_date + 60 trading days.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.benchmarks import eligibility
from src.data.fetch import load_universe

MIN_SURPRISE_PCT = 0.0
HOLD_DAYS = 42          # ~2 months of drift
MAX_WEIGHT = 0.10       # per-name cap; cash absorbs the rest


def generate_weights(prices: pd.DataFrame, events: pd.DataFrame,
                     universe: pd.DataFrame | None = None,
                     min_surprise: float = MIN_SURPRISE_PCT,
                     hold_days: int = HOLD_DAYS,
                     max_weight: float = MAX_WEIGHT) -> pd.DataFrame:
    """Target weights from an earnings-events table
    (columns: ticker, ann_date, surprise_pct)."""
    if universe is None:
        universe = load_universe()

    index = prices.index
    elig = eligibility(prices, universe)
    active = pd.DataFrame(False, index=index, columns=prices.columns)

    events = events.dropna(subset=["surprise_pct"])
    for ticker, ev in events.groupby("ticker"):
        if ticker not in active.columns:
            continue
        ann_dates = ev["ann_date"].sort_values().to_list()
        for i, ann in enumerate(ann_dates):
            row = ev[ev["ann_date"] == ann].iloc[0]
            if row["surprise_pct"] < min_surprise:
                continue
            # first trading day strictly after the announcement date
            pos = index.searchsorted(pd.Timestamp(ann).normalize(), side="right")
            if pos >= len(index):
                continue
            end_pos = pos + hold_days
            # truncate at the next announcement for this ticker
            if i + 1 < len(ann_dates):
                next_pos = index.searchsorted(
                    pd.Timestamp(ann_dates[i + 1]).normalize(), side="right")
                end_pos = min(end_pos, next_pos)
            active.iloc[pos:end_pos, active.columns.get_loc(ticker)] = True

    active &= elig
    n_active = active.sum(axis=1)
    per_name = np.minimum(1.0 / n_active.replace(0, np.nan), max_weight)
    weights = active.astype(float).mul(per_name, axis=0).fillna(0.0)
    return weights
