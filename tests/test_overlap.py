import pandas as pd
import pytest

from src.analysis.overlap import effective_exposure


def test_direct_and_lookthrough_exposure():
    holdings = pd.DataFrame({
        "symbol": ["NVDA", "VOO", "CASH_FUND"],
        "kind": ["stock", "etf", "etf"],
        "market_value": [5_000.0, 20_000.0, 10_000.0],
    })
    etf_weights = {"VOO": {"NVDA": 0.06, "MSFT": 0.07, "XOM": 0.01}}
    exp = effective_exposure(holdings, ["NVDA", "MSFT", "AMD"], etf_weights)

    assert exp.loc["NVDA", "direct"] == 5_000
    assert exp.loc["NVDA", "via_etf"] == pytest.approx(20_000 * 0.06)
    assert exp.loc["MSFT", "total"] == pytest.approx(20_000 * 0.07)
    assert exp.loc["AMD", "total"] == 0.0
    assert exp.loc["NVDA", "pct_of_portfolio"] == pytest.approx(6_200 / 35_000)
