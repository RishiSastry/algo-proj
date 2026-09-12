"""Pairs scan (session 8): find cointegrated pairs honestly.

Protocol:
- Candidates: within-bucket pairs where both names have at least
  MIN_TRAIN_YEARS of joint history before the SPLIT date.
- Train (joint start → SPLIT): Engle-Granger cointegration test on log
  prices, Bonferroni-corrected across ALL pairs tested.
- Test (SPLIT → end): with the hedge ratio FROZEN from train, ADF test
  on the out-of-sample spread. A pair is only "found" if it survives
  both.

The multiple-testing correction is the point: scanning N pairs at
α=0.05 manufactures 0.05·N discoveries from noise.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint

SPLIT = "2018-01-01"
MIN_TRAIN_YEARS = 5.0
ALPHA = 0.05


def candidate_pairs(closes: pd.DataFrame, universe: pd.DataFrame,
                    split: str = SPLIT,
                    min_train_years: float = MIN_TRAIN_YEARS) -> list[tuple[str, str]]:
    split_ts = pd.Timestamp(split)
    pairs = []
    for bucket, members in universe.groupby("bucket").groups.items():
        if bucket == "benchmark":
            continue
        usable = []
        for t in members:
            if t not in closes.columns:
                continue
            s = closes[t].dropna()
            if s.empty or s.index[0] > split_ts:
                continue
            if (split_ts - s.index[0]).days / 365.25 >= min_train_years:
                usable.append(t)
        pairs += list(combinations(sorted(usable), 2))
    return pairs


def hedge_ratio(log_a: pd.Series, log_b: pd.Series) -> tuple[float, float]:
    """OLS log_a = alpha + beta * log_b; returns (alpha, beta)."""
    X = sm.add_constant(log_b.to_numpy())
    model = sm.OLS(log_a.to_numpy(), X).fit()
    return float(model.params[0]), float(model.params[1])


def scan(closes: pd.DataFrame, universe: pd.DataFrame,
         split: str = SPLIT, alpha: float = ALPHA) -> pd.DataFrame:
    """Train cointegration + OOS spread stationarity for all candidates.

    Returns one row per pair with train p-value, the Bonferroni
    threshold used, and the OOS ADF p-value (computed for every pair,
    judged only for train survivors).
    """
    pairs = candidate_pairs(closes, universe, split)
    threshold = alpha / max(len(pairs), 1)
    split_ts = pd.Timestamp(split)

    rows = []
    for a, b in pairs:
        joint = np.log(closes[[a, b]].dropna())
        train, test = joint.loc[:split_ts], joint.loc[split_ts:]
        _, train_p, _ = coint(train[a], train[b])
        const, beta = hedge_ratio(train[a], train[b])
        spread_test = test[a] - (const + beta * test[b])
        oos_p = (adfuller(spread_test, result_object=False)[1]
                 if len(spread_test) > 252 else np.nan)
        rows.append({
            "pair": f"{a}/{b}",
            "bucket": universe.loc[a, "bucket"],
            "train_years": round((split_ts - joint.index[0]).days / 365.25, 1),
            "train_coint_p": train_p,
            "beta": round(beta, 3),
            "oos_adf_p": oos_p,
            "train_pass": train_p < threshold,
        })
    out = pd.DataFrame(rows).sort_values("train_coint_p")
    out.attrs["bonferroni_threshold"] = threshold
    out.attrs["n_pairs"] = len(pairs)
    return out
