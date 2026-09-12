"""Summary statistics for a daily simple-return series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.returns import TRADING_DAYS, drawdown_series, equity_curve


def summary_stats(returns: pd.Series, rf: float = 0.0) -> dict:
    """CAGR, annualized vol, Sharpe, Sortino, max drawdown, Calmar.

    `returns` are daily simple returns; `rf` is an annualized risk-free
    rate (0 for now per plan.md).
    """
    r = returns.dropna()
    if r.empty:
        return {k: np.nan for k in
                ["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "calmar",
                 "n_days", "start", "end"]}

    years = len(r) / TRADING_DAYS
    growth = float(equity_curve(r).iloc[-1])
    cagr = growth ** (1 / years) - 1 if growth > 0 else np.nan

    rf_daily = (1 + rf) ** (1 / TRADING_DAYS) - 1
    excess = r - rf_daily
    ann_vol = float(r.std() * np.sqrt(TRADING_DAYS))
    sharpe = float(excess.mean() / excess.std() * np.sqrt(TRADING_DAYS)) if excess.std() > 0 else np.nan

    downside = excess[excess < 0]
    downside_dev = float(np.sqrt((downside**2).sum() / len(excess)) * np.sqrt(TRADING_DAYS))
    sortino = float(excess.mean() * TRADING_DAYS / downside_dev) if downside_dev > 0 else np.nan

    max_dd = float(drawdown_series(r).min())
    calmar = cagr / abs(max_dd) if max_dd < 0 and not np.isnan(cagr) else np.nan

    return {
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "n_days": len(r),
        "start": r.index[0].date(),
        "end": r.index[-1].date(),
    }


def summary_table(returns_panel: pd.DataFrame, rf: float = 0.0) -> pd.DataFrame:
    """summary_stats for each column of a returns panel, as a DataFrame."""
    rows = {col: summary_stats(returns_panel[col], rf=rf) for col in returns_panel.columns}
    return pd.DataFrame(rows).T


def format_summary_table(table: pd.DataFrame) -> pd.DataFrame:
    """Human-readable version of summary_table output."""
    out = table.copy()
    for col in ["cagr", "ann_vol", "max_drawdown"]:
        out[col] = out[col].map(lambda v: f"{v:.1%}" if pd.notna(v) else "—")
    for col in ["sharpe", "sortino", "calmar"]:
        out[col] = out[col].map(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
    return out
