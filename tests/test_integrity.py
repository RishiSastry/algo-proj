import numpy as np
import pandas as pd
import pytest

from src.data import integrity


@pytest.fixture
def dates():
    return pd.bdate_range("2024-01-01", periods=40)


def make_prices(closes: pd.DataFrame) -> pd.DataFrame:
    fields = {f: closes for f in ["Open", "High", "Low", "Close"]}
    fields["Volume"] = closes * 0 + 1_000
    panel = pd.concat(fields, axis=1)
    panel.columns.names = ["field", "ticker"]
    return panel


def test_bad_prices_flags_zero_and_negative(dates):
    closes = pd.DataFrame({"AAA": 100.0, "BBB": 50.0}, index=dates)
    closes.iloc[3, 0] = 0.0
    closes.iloc[5, 1] = -1.0
    bad = integrity.bad_prices(make_prices(closes))
    assert set(bad["ticker"]) == {"AAA", "BBB"}
    assert len(bad) == 8  # 2 bad values × 4 price fields


def test_long_gaps_detects_only_gaps_over_threshold(dates):
    closes = pd.DataFrame({"AAA": 100.0, "BBB": 100.0}, index=dates)
    closes.iloc[10:17, 0] = np.nan  # 7-day gap -> flagged
    closes.iloc[20:23, 1] = np.nan  # 3-day gap -> not flagged
    gaps = integrity.long_gaps(closes)
    assert list(gaps["ticker"]) == ["AAA"]
    assert gaps.iloc[0]["n_days"] == 7


def test_long_gaps_ignores_pre_listing_nans(dates):
    closes = pd.DataFrame({"NEW": 100.0}, index=dates)
    closes.iloc[:20, 0] = np.nan  # not yet listed — not a gap
    assert integrity.long_gaps(closes).empty


def test_suspicious_moves(dates):
    closes = pd.DataFrame({"AAA": 100.0}, index=dates)
    closes.iloc[10:, 0] = 160.0  # +60% single-day move
    moves = integrity.suspicious_moves(closes)
    assert len(moves) == 1
    assert moves.iloc[0]["ticker"] == "AAA"
    assert moves.iloc[0]["return"] == pytest.approx(0.60)


def test_missing_trading_days_respects_ipo_date(dates):
    closes = pd.DataFrame({"AAA": 100.0}, index=dates)
    closes.iloc[15, 0] = np.nan  # one hole inside history
    closes.iloc[:5, 0] = np.nan  # pre-IPO — must not count
    universe = pd.DataFrame({"ipo_date": [dates[5]]}, index=["AAA"])
    missing = integrity.missing_trading_days(closes, universe)
    assert missing == {"AAA": 1}
