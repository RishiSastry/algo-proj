"""Dip-buying in uptrends (strategy family #2).

Pre-registered in research/2026-09-13-dipbuy-prereg.md BEFORE any
backtest. Rule: while the basket is above its 210d MA, a 5-day basket
return ≤ -5% triggers a full-basket position held 10 trading days
(re-triggers restart the clock; the gate turning down forces exit).
Cash otherwise. Signals daily at the close; the engine adds the
standard one-day execution lag.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.benchmarks import eligibility, masked_closes
from src.data.fetch import load_universe
from src.strategies.basket_timing import MA_WINDOW, basket_index

DIP_WINDOW = 5
DIP_THRESHOLD = -0.05
HOLD_DAYS = 10


def dip_signal(index: pd.Series, dip_window: int = DIP_WINDOW,
               threshold: float = DIP_THRESHOLD,
               hold_days: int = HOLD_DAYS,
               ma_window: int = MA_WINDOW) -> pd.Series:
    """Daily 0/1 exposure scalar for the sleeve."""
    gate = index > index.rolling(ma_window).mean()
    trigger = (index.pct_change(dip_window) <= threshold) & gate

    on = np.zeros(len(index))
    remaining = 0
    for i in range(len(index)):
        if trigger.iloc[i]:
            remaining = hold_days
        if not gate.iloc[i]:
            remaining = 0
        if remaining > 0:
            on[i] = 1.0
            remaining -= 1
    return pd.Series(on, index=index.index)


def generate_weights(prices: pd.DataFrame,
                     universe: pd.DataFrame | None = None,
                     dip_window: int = DIP_WINDOW,
                     threshold: float = DIP_THRESHOLD,
                     hold_days: int = HOLD_DAYS) -> pd.DataFrame:
    """EW basket weights during post-dip holds, cash otherwise."""
    if universe is None:
        universe = load_universe()

    masked = masked_closes(prices, universe)
    elig = eligibility(prices, universe)
    index = basket_index(prices, universe)
    scalar = dip_signal(index, dip_window, threshold, hold_days)

    live = elig & masked.notna()
    n = live.sum(axis=1)
    ew = live.astype(float).div(n.where(n > 0, np.nan), axis=0).fillna(0.0)
    return ew.mul(scalar, axis=0)
