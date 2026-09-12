"""Return-series primitives.

Convention (CLAUDE.md): log returns for analysis, simple returns for P&L.
All functions accept a Series or DataFrame of prices/returns and return
the same shape.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def simple_returns(prices):
    return prices.pct_change()


def log_returns(prices):
    return np.log(prices).diff()


def rolling_vol(returns, window: int = 21, annualize: bool = True):
    vol = returns.rolling(window).std()
    return vol * np.sqrt(TRADING_DAYS) if annualize else vol


def equity_curve(returns):
    """Cumulative growth of $1 from a simple-return series."""
    return (1 + returns.fillna(0)).cumprod()


def drawdown_series(returns):
    """Drawdown (≤ 0) at each date, from simple returns."""
    curve = equity_curve(returns)
    return curve / curve.cummax() - 1
