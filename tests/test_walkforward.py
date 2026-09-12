import numpy as np
import pandas as pd
import pytest

from src.backtest.walkforward import walk_forward


def test_walk_forward_switches_to_regime_winner():
    # Param A is good in the first half, param B in the second. With
    # short folds the selector must ride A early and switch to B.
    n = 2000
    idx = pd.bdate_range("2015-01-01", periods=n)
    a = pd.Series(np.r_[np.full(n // 2, 0.002), np.full(n - n // 2, -0.002)], index=idx)
    b = pd.Series(np.r_[np.full(n // 2, -0.002), np.full(n - n // 2, 0.002)], index=idx)
    rng = np.random.default_rng(0)
    noise = pd.Series(rng.normal(0, 1e-4, n), index=idx)

    result = walk_forward({"A": a + noise, "B": b + noise},
                          train_days=200, test_days=100)
    chosen = result.fold_log["chosen"]
    assert chosen.iloc[0] == "A"
    assert chosen.iloc[-1] == "B"


def test_oos_is_exactly_the_chosen_series_slices():
    idx = pd.bdate_range("2020-01-01", periods=400)
    rng = np.random.default_rng(1)
    series = {k: pd.Series(rng.normal(0.0005, 0.01, 400), index=idx) for k in ["A", "B"]}
    result = walk_forward(series, train_days=200, test_days=100)

    for _, fold in result.fold_log.iterrows():
        expected = series[fold["chosen"]].loc[fold["test_start"]:fold["test_end"]]
        actual = result.oos_returns.loc[fold["test_start"]:fold["test_end"]]
        pd.testing.assert_series_equal(actual, expected, check_names=False)


def test_oos_never_overlaps_training_data():
    idx = pd.bdate_range("2020-01-01", periods=500)
    series = {"A": pd.Series(0.001, index=idx)}
    result = walk_forward(series, train_days=300, test_days=100)
    assert result.oos_returns.index[0] == idx[300]  # first OOS day is post-train


def test_too_short_history_raises():
    idx = pd.bdate_range("2020-01-01", periods=100)
    with pytest.raises(ValueError):
        walk_forward({"A": pd.Series(0.001, index=idx)}, train_days=300, test_days=100)
