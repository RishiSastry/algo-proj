"""Cross-sectional momentum v0.

Rule (plan.md step 9): at each month-end, rank the eligible universe by
trailing 6-month return skipping the most recent month (126 trading
days ending 21 days ago), hold the top third equal-weight, rebalance
monthly.

All parameters are named constants — they are hypotheses, not tuned
values (do NOT optimize them in-sample).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.benchmarks import eligibility, masked_closes
from src.data.fetch import load_universe

LOOKBACK_DAYS = 126   # ~6 months
SKIP_DAYS = 21        # skip most recent month (short-term reversal)
TOP_FRACTION = 1 / 3
MIN_NAMES = 3         # below this many candidates, stay in cash


def momentum_score(closes: pd.DataFrame, lookback: int = LOOKBACK_DAYS,
                   skip: int = SKIP_DAYS) -> pd.DataFrame:
    """Trailing `lookback` return ending `skip` days ago. The value at
    date t uses only closes up to t (both operands are lagged)."""
    return closes.shift(skip) / closes.shift(skip + lookback) - 1


def generate_weights(prices: pd.DataFrame,
                     universe: pd.DataFrame | None = None,
                     lookback: int = LOOKBACK_DAYS,
                     skip: int = SKIP_DAYS,
                     top_fraction: float = TOP_FRACTION) -> pd.DataFrame:
    """Target weights (dates × tickers, rows sum ≤ 1.0).

    `prices` is an adjusted-close panel (dates × tickers) of the
    tradable universe. The weight row at date t is decided at the close
    of t; the engine handles the one-day execution delay.
    """
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
            k = int(np.ceil(len(candidates) * top_fraction))
            top = candidates.nlargest(k).index
            row[top] = 1.0 / k
        weights.loc[t] = row

    # hold targets between rebalances; cash (all-zero) before first one
    return weights.ffill().fillna(0.0)
