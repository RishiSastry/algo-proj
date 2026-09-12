import numpy as np
import pandas as pd
import pytest

from src.analysis.returns import drawdown_series, equity_curve, log_returns, simple_returns
from src.analysis.stats import summary_stats


def test_simple_and_log_returns_agree_to_first_order():
    prices = pd.Series([100.0, 101.0, 100.5, 102.0],
                       index=pd.bdate_range("2024-01-01", periods=4))
    s, l = simple_returns(prices), log_returns(prices)
    assert np.allclose(np.log1p(s.dropna()), l.dropna())


def test_equity_curve_and_drawdown():
    r = pd.Series([0.10, -0.50, 0.0], index=pd.bdate_range("2024-01-01", periods=3))
    curve = equity_curve(r)
    assert curve.iloc[-1] == pytest.approx(1.10 * 0.50)
    assert drawdown_series(r).min() == pytest.approx(-0.50)


def test_summary_stats_constant_positive_return():
    n = 252
    r = pd.Series(0.001, index=pd.bdate_range("2020-01-01", periods=n))
    stats = summary_stats(r)
    assert stats["cagr"] == pytest.approx(1.001**252 - 1, rel=1e-6)
    assert stats["max_drawdown"] == 0.0
    assert stats["ann_vol"] == pytest.approx(0.0)
