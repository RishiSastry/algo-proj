"""Factor structure of the universe: how much is this really one bet?

- rolling 60-day average pairwise correlation
- rolling fraction of variance explained by the first principal
  component of the correlation matrix
"""

from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW = 60
MIN_TICKERS = 5


def _complete_window(returns: pd.DataFrame, end_pos: int, window: int) -> pd.DataFrame:
    chunk = returns.iloc[end_pos - window + 1 : end_pos + 1]
    return chunk.dropna(axis=1)


def rolling_factor_stats(returns: pd.DataFrame, window: int = WINDOW,
                         step: int = 1) -> pd.DataFrame:
    """Per date: average pairwise correlation, PC1 variance share, and
    the number of tickers with complete data in the window."""
    rows = []
    for pos in range(window - 1, len(returns), step):
        chunk = _complete_window(returns, pos, window)
        n = chunk.shape[1]
        if n < MIN_TICKERS:
            continue
        corr = chunk.corr().to_numpy()
        off_diag = corr[~np.eye(n, dtype=bool)]
        eigvals = np.linalg.eigvalsh(corr)
        rows.append({
            "date": returns.index[pos],
            "avg_pairwise_corr": off_diag.mean(),
            "pc1_share": eigvals[-1] / n,
            "n_tickers": n,
        })
    return pd.DataFrame(rows).set_index("date")


def full_sample_correlation(returns: pd.DataFrame, min_obs: int = 252) -> pd.DataFrame:
    """Pairwise correlation using all overlapping data, tickers with at
    least `min_obs` observations."""
    keep = [c for c in returns.columns if returns[c].notna().sum() >= min_obs]
    return returns[keep].corr(min_periods=min_obs)
