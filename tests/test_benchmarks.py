import numpy as np
import pandas as pd
import pytest

from src.analysis.benchmarks import eligibility, equal_weight_returns, masked_closes


@pytest.fixture
def dates():
    return pd.bdate_range("2023-01-02", periods=200)


def test_masked_closes_nans_pre_ipo(dates):
    closes = pd.DataFrame({"AAA": 100.0}, index=dates)
    universe = pd.DataFrame({"ipo_date": [dates[50]]}, index=["AAA"])
    masked = masked_closes(closes, universe)
    assert masked["AAA"].iloc[:50].isna().all()
    assert masked["AAA"].iloc[50:].notna().all()


def test_eligibility_waits_seasoning_days(dates):
    closes = pd.DataFrame({"AAA": 100.0, "NEW": 100.0}, index=dates)
    universe = pd.DataFrame({"ipo_date": [dates[0], dates[100]]}, index=["AAA", "NEW"])
    elig = eligibility(closes, universe, seasoning_days=60)
    assert elig["AAA"].iloc[60]
    assert not elig["AAA"].iloc[59]
    assert not elig["NEW"].iloc[159]
    assert elig["NEW"].iloc[160]


def test_equal_weight_flat_prices_zero_return(dates):
    closes = pd.DataFrame({"AAA": 100.0, "BBB": 50.0}, index=dates)
    universe = pd.DataFrame({"ipo_date": [dates[0]] * 2}, index=["AAA", "BBB"])
    rets = equal_weight_returns(closes, universe, seasoning_days=0)
    assert np.allclose(rets, 0.0)


def test_equal_weight_two_tickers_averages(dates):
    # AAA +1%/day, BBB flat: first day after a rebalance the portfolio
    # return must be exactly the 0.5% average.
    aaa = 100 * (1.01 ** np.arange(len(dates)))
    closes = pd.DataFrame({"AAA": aaa, "BBB": 50.0}, index=dates)
    universe = pd.DataFrame({"ipo_date": [dates[0]] * 2}, index=["AAA", "BBB"])
    rets = equal_weight_returns(closes, universe, seasoning_days=0)
    month_ends = closes.index.to_series().groupby(closes.index.to_period("M")).last()
    first_day_after = rets.index[rets.index.get_loc(month_ends.iloc[0]) + 1]
    assert rets.loc[first_day_after] == pytest.approx(0.005)
