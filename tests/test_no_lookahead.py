"""No-lookahead guarantees (CLAUDE.md #3).

The engine must make it impossible for a weight decided at date t to
earn date t's return, and future prices must never influence past
portfolio returns.
"""

import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import run_backtest


def make_panel(closes: pd.DataFrame) -> pd.DataFrame:
    panel = pd.concat({"Close": closes, "Volume": closes * 0 + 1e6}, axis=1)
    panel.columns.names = ["field", "ticker"]
    return panel


@pytest.fixture
def dates():
    return pd.bdate_range("2024-01-01", periods=30)


def test_cheating_weight_cannot_capture_same_day_return(dates):
    # One huge up day at position 15. A "clairvoyant" strategy that puts
    # on full weight AT that date must not receive that day's return.
    prices = pd.Series(100.0, index=dates)
    prices.iloc[15:] = 200.0  # +100% on day 15
    closes = pd.DataFrame({"AAA": prices})
    weights = pd.DataFrame(0.0, index=dates, columns=["AAA"])
    weights.iloc[15] = 1.0

    result = run_backtest(weights, make_panel(closes))
    assert result.gross_returns.iloc[15] == 0.0  # jump day: no position yet
    assert result.gross_returns.iloc[16] == 0.0  # held during a flat day


def test_weight_at_t_earns_return_of_t_plus_1(dates):
    prices = pd.Series(100.0, index=dates)
    prices.iloc[16:] = 110.0  # +10% on day 16
    closes = pd.DataFrame({"AAA": prices})
    weights = pd.DataFrame(0.0, index=dates, columns=["AAA"])
    weights.iloc[15] = 1.0  # decided at close of day 15

    result = run_backtest(weights, make_panel(closes))
    assert result.gross_returns.iloc[16] == pytest.approx(0.10)


def test_future_price_change_does_not_alter_past_returns(dates):
    rng = np.random.default_rng(7)
    closes = pd.DataFrame(
        {t: 100 * np.cumprod(1 + rng.normal(0, 0.02, len(dates))) for t in ["AAA", "BBB"]},
        index=dates,
    )
    weights = pd.DataFrame(0.5, index=dates, columns=["AAA", "BBB"])

    base = run_backtest(weights, make_panel(closes)).net_returns
    bumped = closes.copy()
    bumped.iloc[-1] *= 1.5  # change only the final day's prices
    after = run_backtest(weights, make_panel(bumped)).net_returns

    # everything before the final day must be identical
    pd.testing.assert_series_equal(base.iloc[:-1], after.iloc[:-1])


def test_costs_charged_on_turnover(dates):
    closes = pd.DataFrame({"AAA": 100.0}, index=dates)
    weights = pd.DataFrame(0.0, index=dates, columns=["AAA"])
    weights.iloc[5:] = 1.0  # single buy, then hold

    result = run_backtest(weights, make_panel(closes))
    assert result.costs.iloc[6] > 0  # executed on day 6
    assert result.costs.iloc[7:].sum() == 0.0
    assert result.net_returns.iloc[6] < 0  # flat prices, so net = -cost


def test_weight_rows_over_one_rejected(dates):
    closes = pd.DataFrame({"AAA": 100.0, "BBB": 100.0}, index=dates)
    weights = pd.DataFrame(0.6, index=dates, columns=["AAA", "BBB"])
    with pytest.raises(ValueError):
        run_backtest(weights, make_panel(closes))
