"""Parameter-sensitivity surfaces (session 5 protocol).

Purpose: measure whether a strategy's performance is a plateau (robust)
or a spike (fragile/overfit) in its parameter neighborhood. Surfaces
are diagnostics — the maximum of a surface is NEVER promoted to "the"
parameter set (that would be point optimization, the thing this module
exists to prevent).
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def net_sharpe(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) < 252 or r.std() == 0:
        return np.nan
    return float(r.mean() / r.std() * np.sqrt(TRADING_DAYS))


def surface(grid: dict[str, list], run) -> pd.DataFrame:
    """Evaluate `run(**params) -> float` over the cartesian grid.

    Returns a tidy DataFrame with one row per grid point and a `value`
    column. Pivot for heatmaps.
    """
    names = list(grid)
    rows = []
    for combo in itertools.product(*grid.values()):
        params = dict(zip(names, combo))
        rows.append({**params, "value": run(**params)})
    return pd.DataFrame(rows)


def plateau_stats(surf: pd.DataFrame) -> dict:
    """Fragility summary of a surface's `value` column."""
    v = surf["value"].dropna()
    return {
        "n": len(v),
        "min": float(v.min()),
        "median": float(v.median()),
        "max": float(v.max()),
        "iqr": float(v.quantile(0.75) - v.quantile(0.25)),
        "share_above_zero": float((v > 0).mean()),
    }
