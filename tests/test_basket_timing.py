import numpy as np
import pandas as pd
import pytest

from src.strategies.basket_timing import (ew_target_weights,
                                          generate_weights_trend,
                                          generate_weights_voltarget)


@pytest.fixture
def dates():
    return pd.bdate_range("2020-01-01", periods=600)


@pytest.fixture
def universe(dates):
    return pd.DataFrame({"ipo_date": [dates[0], dates[0]]}, index=["AAA", "BBB"])


def test_ew_target_weights_equal_split(dates, universe):
    prices = pd.DataFrame({"AAA": 100.0, "BBB": 50.0}, index=dates)
    w = ew_target_weights(prices, universe)
    late = w.iloc[100]  # past seasoning + first rebalance
    assert late["AAA"] == pytest.approx(0.5)
    assert late["BBB"] == pytest.approx(0.5)


def test_trend_full_invested_in_uptrend_cash_in_downtrend(dates, universe):
    n = len(dates)
    up_down = np.r_[100 * 1.005 ** np.arange(n // 2),
                    100 * 1.005 ** (n // 2) * 0.99 ** np.arange(n - n // 2)]
    prices = pd.DataFrame({"AAA": up_down, "BBB": up_down}, index=dates)
    w = generate_weights_trend(prices, universe, ma_window=60)
    assert w.iloc[300].sum() == pytest.approx(1.0)   # deep in the uptrend
    assert w.iloc[-1].sum() == 0.0                   # deep in the downtrend


def test_voltarget_scales_down_when_vol_high(dates, universe):
    rng = np.random.default_rng(3)
    calm = 100 * np.cumprod(1 + rng.normal(0.0005, 0.004, len(dates)))
    prices = pd.DataFrame({"AAA": calm, "BBB": calm}, index=dates)
    w_calm = generate_weights_voltarget(prices, universe, target_vol=0.20)
    assert w_calm.iloc[-1].sum() == pytest.approx(1.0)  # calm: capped at full

    wild = 100 * np.cumprod(1 + rng.normal(0.0005, 0.04, len(dates)))
    prices_wild = pd.DataFrame({"AAA": wild, "BBB": wild}, index=dates)
    w_wild = generate_weights_voltarget(prices_wild, universe, target_vol=0.20)
    assert 0 < w_wild.iloc[-1].sum() < 0.5  # ~60% realized vol -> ~1/3 exposure


def test_weights_never_exceed_budget(dates, universe):
    rng = np.random.default_rng(4)
    prices = pd.DataFrame(
        {t: 100 * np.cumprod(1 + rng.normal(0.001, 0.02, len(dates))) for t in ["AAA", "BBB"]},
        index=dates)
    for w in [generate_weights_trend(prices, universe, ma_window=60),
              generate_weights_voltarget(prices, universe)]:
        assert (w.sum(axis=1) <= 1.0 + 1e-9).all()
        assert (w >= 0).all().all()
