"""Transaction-cost model (CLAUDE.md #2).

Cost per side = SLIPPAGE_BPS + estimated half bid-ask spread.
Daily bars carry no quote data, so the half-spread is estimated from
average daily dollar volume — a coarse, deliberately conservative
liquidity ladder. Revisit when real quote data is available.
"""

from __future__ import annotations

import pandas as pd

SLIPPAGE_BPS = 5.0

# (min average daily dollar volume, half-spread in bps)
HALF_SPREAD_LADDER = [
    (5e9, 1.0),
    (1e9, 2.5),
    (250e6, 5.0),
    (0.0, 10.0),
]


def half_spread_bps(avg_dollar_volume: pd.Series) -> pd.Series:
    """Per-ticker half-spread estimate from average daily dollar volume."""
    def _lookup(adv):
        for floor, bps in HALF_SPREAD_LADDER:
            if adv >= floor:
                return bps
        return HALF_SPREAD_LADDER[-1][1]
    return avg_dollar_volume.fillna(0.0).map(_lookup)


def cost_per_side(avg_dollar_volume: pd.Series) -> pd.Series:
    """Total one-way cost in return units (not bps) per ticker."""
    return (SLIPPAGE_BPS + half_spread_bps(avg_dollar_volume)) / 1e4


def transaction_costs(executed_weights: pd.DataFrame,
                      per_side_cost: pd.Series) -> pd.Series:
    """Daily cost drag: sum over tickers of |Δweight| × one-way cost."""
    dw = executed_weights.fillna(0.0).diff()
    if len(dw):
        dw.iloc[0] = executed_weights.iloc[0].fillna(0.0)  # initial buy-in
    aligned = per_side_cost.reindex(dw.columns).fillna(per_side_cost.max())
    return (dw.abs() * aligned).sum(axis=1)
