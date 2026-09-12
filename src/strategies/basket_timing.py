"""Time-series strategies on the equal-weight basket (session 7).

Rationale (factor-structure + robustness notes): the universe is one
dominant factor, and no cross-sectional signal survived testing — so
manage the factor itself. Two pre-registered rules, both operating on
the EW basket and evaluated at month-end (same schedule as everything
else; the engine adds the one-day execution lag):

1. Trend filter: hold the basket when its index is above its trailing
   moving average, else cash. Default MA_WINDOW = 210 trading days
   (the classic 10-month rule).
2. Vol targeting: scale basket exposure by target_vol / realized vol,
   capped at 1.0 (no leverage). Defaults: 20% target, 63-day window.

Both are long-only, no leverage; rows sum ≤ 1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.benchmarks import eligibility, equal_weight_returns, masked_closes
from src.analysis.returns import TRADING_DAYS, equity_curve
from src.data.fetch import load_universe

MA_WINDOW = 210
TARGET_VOL = 0.20
VOL_WINDOW = 63


def _month_ends(index: pd.DatetimeIndex) -> pd.Series:
    return index.to_series().groupby(index.to_period("M")).last()


def ew_target_weights(prices: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    """Month-end 1/N weights over eligible tickers, held between
    rebalances (the weights version of the EW benchmark)."""
    masked = masked_closes(prices, universe)
    elig = eligibility(prices, universe)
    weights = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    for t in _month_ends(prices.index):
        members = [c for c in prices.columns
                   if elig.loc[t, c] and pd.notna(masked.loc[t, c])]
        row = pd.Series(0.0, index=prices.columns)
        if members:
            row[members] = 1.0 / len(members)
        weights.loc[t] = row
    return weights.ffill().fillna(0.0)


def basket_index(prices: pd.DataFrame, universe: pd.DataFrame) -> pd.Series:
    """Growth-of-$1 index of the EW basket (backward-looking only)."""
    return equity_curve(equal_weight_returns(prices, universe))


def _scaled_ew(prices: pd.DataFrame, universe: pd.DataFrame,
               scalar_at_month_end: pd.Series) -> pd.DataFrame:
    """EW weights times a month-end signal scalar, held between
    rebalances."""
    ew = ew_target_weights(prices, universe)
    scalar = pd.Series(np.nan, index=prices.index)
    month_ends = _month_ends(prices.index)
    scalar.loc[month_ends] = scalar_at_month_end.reindex(month_ends).to_numpy()
    scalar = scalar.ffill().fillna(0.0)
    return ew.mul(scalar, axis=0)


def generate_weights_trend(prices: pd.DataFrame,
                           universe: pd.DataFrame | None = None,
                           ma_window: int = MA_WINDOW) -> pd.DataFrame:
    """In the basket when its index closes above its trailing MA."""
    if universe is None:
        universe = load_universe()
    index = basket_index(prices, universe)
    signal = (index > index.rolling(ma_window).mean()).astype(float)
    return _scaled_ew(prices, universe, signal)


def generate_weights_voltarget(prices: pd.DataFrame,
                               universe: pd.DataFrame | None = None,
                               target_vol: float = TARGET_VOL,
                               vol_window: int = VOL_WINDOW) -> pd.DataFrame:
    """Basket exposure = min(1, target_vol / realized vol)."""
    if universe is None:
        universe = load_universe()
    rets = equal_weight_returns(prices, universe)
    realized = rets.rolling(vol_window).std() * np.sqrt(TRADING_DAYS)
    scalar = (target_vol / realized).clip(upper=1.0).fillna(0.0)
    return _scaled_ew(prices, universe, scalar)


def generate_weights_combo(prices: pd.DataFrame,
                           universe: pd.DataFrame | None = None,
                           ma_window: int = MA_WINDOW,
                           target_vol: float = TARGET_VOL,
                           vol_window: int = VOL_WINDOW) -> pd.DataFrame:
    """Session 9 pre-registered combination: exposure =
    trend_signal × min(1, target_vol / realized vol). In a downtrend
    the book is cash regardless of vol; in an uptrend it is vol-scaled."""
    if universe is None:
        universe = load_universe()
    index = basket_index(prices, universe)
    trend = (index > index.rolling(ma_window).mean()).astype(float)
    rets = equal_weight_returns(prices, universe)
    realized = rets.rolling(vol_window).std() * np.sqrt(TRADING_DAYS)
    volscale = (target_vol / realized).clip(upper=1.0)
    return _scaled_ew(prices, universe, (trend * volscale).fillna(0.0))
