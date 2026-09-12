"""Long-short cross-sectional momentum v0.

Motivation (see 2026-09-12-factor-structure.md): ~45% of universe
variance is one common factor, so long-only tilts are mostly the sector
bet. Going long the top third and short the bottom third nets out most
of the factor and isolates the cross-sectional signal.

Rule (pre-registered, untuned): same 6-1 momentum score and month-end
schedule as momentum_xs. Long top third at +0.5 total, short bottom
third at -0.5 total, equal weight within each leg. Gross = 1.0, net = 0.
Cash earns nothing; borrow costs are NOT modeled (documented).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.benchmarks import eligibility, masked_closes
from src.data.fetch import load_universe
from src.strategies.momentum_xs import (LOOKBACK_DAYS, SKIP_DAYS, TOP_FRACTION,
                                        momentum_score)

LEG_BUDGET = 0.5   # each leg's gross weight
MIN_NAMES = 6      # need enough names to form both legs


def generate_weights(prices: pd.DataFrame,
                     universe: pd.DataFrame | None = None,
                     lookback: int = LOOKBACK_DAYS,
                     skip: int = SKIP_DAYS,
                     fraction: float = TOP_FRACTION,
                     leg_budget: float = LEG_BUDGET) -> pd.DataFrame:
    """Dollar-neutral target weights (rows: net 0, gross ≤ 1)."""
    if universe is None:
        universe = load_universe()

    closes = masked_closes(prices, universe)
    elig = eligibility(prices, universe)
    score = momentum_score(closes, lookback=lookback, skip=skip)

    month = closes.index.to_period("M")
    month_ends = closes.index.to_series().groupby(month).last()

    weights = pd.DataFrame(np.nan, index=closes.index, columns=closes.columns)
    for t in month_ends:
        candidates = score.loc[t].where(elig.loc[t]).dropna()
        row = pd.Series(0.0, index=closes.columns)
        if len(candidates) >= MIN_NAMES:
            k = int(np.ceil(len(candidates) * fraction))
            row[candidates.nlargest(k).index] = leg_budget / k
            row[candidates.nsmallest(k).index] = -leg_budget / k
        weights.loc[t] = row

    return weights.ffill().fillna(0.0)
