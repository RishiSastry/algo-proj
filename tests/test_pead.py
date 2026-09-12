import pandas as pd
import pytest

from src.strategies.pead import generate_weights


@pytest.fixture
def dates():
    return pd.bdate_range("2024-01-01", periods=120)


@pytest.fixture
def prices(dates):
    return pd.DataFrame({"AAA": 100.0, "BBB": 100.0}, index=dates)


@pytest.fixture
def universe(dates):
    return pd.DataFrame({"ipo_date": [dates[0], dates[0]]}, index=["AAA", "BBB"])


def test_entry_is_day_after_announcement(dates, prices, universe):
    events = pd.DataFrame({"ticker": ["AAA"], "ann_date": [dates[70]], "surprise_pct": [5.0]})
    w = generate_weights(prices, events, universe, hold_days=10)
    assert w.loc[dates[70], "AAA"] == 0.0       # announcement day: no signal yet
    assert w.loc[dates[71], "AAA"] > 0.0        # first day after
    assert w.loc[dates[80], "AAA"] > 0.0        # still held (10-day window)
    assert w.loc[dates[81], "AAA"] == 0.0       # expired


def test_negative_surprise_ignored(dates, prices, universe):
    events = pd.DataFrame({"ticker": ["AAA"], "ann_date": [dates[70]], "surprise_pct": [-3.0]})
    w = generate_weights(prices, events, universe)
    assert (w["AAA"] == 0).all()


def test_next_announcement_truncates_hold(dates, prices, universe):
    events = pd.DataFrame({
        "ticker": ["AAA", "AAA"],
        "ann_date": [dates[70], dates[75]],
        "surprise_pct": [5.0, -1.0],  # second print is a miss -> exit
    })
    w = generate_weights(prices, events, universe, hold_days=42)
    assert w.loc[dates[71], "AAA"] > 0.0
    assert w.loc[dates[76], "AAA"] == 0.0  # truncated at next print


def test_seasoning_blocks_fresh_listings(dates, prices, universe):
    universe.loc["AAA", "ipo_date"] = dates[60]  # eligible only from day 120 — never
    events = pd.DataFrame({"ticker": ["AAA"], "ann_date": [dates[70]], "surprise_pct": [9.0]})
    w = generate_weights(prices, events, universe)
    assert (w["AAA"] == 0).all()


def test_weight_cap_and_budget(dates, prices, universe):
    events = pd.DataFrame({
        "ticker": ["AAA", "BBB"],
        "ann_date": [dates[70], dates[70]],
        "surprise_pct": [5.0, 5.0],
    })
    w = generate_weights(prices, events, universe, max_weight=0.10)
    row = w.loc[dates[71]]
    assert row["AAA"] == pytest.approx(0.10)  # capped, not 1/2
    assert row.sum() <= 1.0 + 1e-12
