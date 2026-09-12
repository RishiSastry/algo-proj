"""Walk-forward validation (CLAUDE.md #6).

Protocol: split the calendar into rolling folds. In each fold, every
candidate parameter set is scored on the TRAIN window only; the winner's
returns over the following TEST window are collected as out-of-sample.
The stitched OOS series is the only thing reported as a finding.

Design note: each parameter set's full-history net-return series is
computed ONCE (weights at date t provably use only data ≤ t — see
tests/test_no_lookahead.py), then folds merely slice it. Selection at
fold k therefore only ever sees returns from dates inside its train
window. Not modeled: the one-off turnover cost of switching parameter
sets at a fold boundary (small at quarterly test windows; documented).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _sharpe(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 20 or r.std() == 0:
        return -np.inf
    return float(r.mean() / r.std() * np.sqrt(TRADING_DAYS))


@dataclass
class WalkForwardResult:
    oos_returns: pd.Series            # stitched out-of-sample net returns
    fold_log: pd.DataFrame            # per fold: window, chosen params, scores

    def chosen_params(self) -> pd.Series:
        return self.fold_log["chosen"]


def walk_forward(returns_by_params: dict[str, pd.Series],
                 train_days: int = 3 * TRADING_DAYS,
                 test_days: int = TRADING_DAYS // 2,
                 score=_sharpe) -> WalkForwardResult:
    """Select among precomputed full-history return series, fold by fold.

    returns_by_params: {param-label: daily net returns over full history}.
    All series must share one calendar index.
    """
    labels = list(returns_by_params)
    frame = pd.concat([returns_by_params[k].rename(k) for k in labels], axis=1)
    index = frame.index

    folds = []
    oos_parts = []
    start = 0
    while start + train_days + test_days <= len(index):
        tr = frame.iloc[start : start + train_days]
        te = frame.iloc[start + train_days : start + train_days + test_days]
        train_scores = {k: score(tr[k]) for k in labels}
        chosen = max(train_scores, key=train_scores.get)
        oos_parts.append(te[chosen])
        folds.append({
            "train_start": tr.index[0], "train_end": tr.index[-1],
            "test_start": te.index[0], "test_end": te.index[-1],
            "chosen": chosen,
            "train_score": train_scores[chosen],
            "test_score": score(te[chosen]),
        })
        start += test_days

    if not folds:
        raise ValueError("history too short for one train+test fold")

    return WalkForwardResult(
        oos_returns=pd.concat(oos_parts).rename("walk_forward_oos"),
        fold_log=pd.DataFrame(folds),
    )
