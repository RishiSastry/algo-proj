"""Vectorized backtest engine v0.

Contract (CLAUDE.md):
- Strategies produce target weights (dates × tickers, rows sum ≤ 1.0),
  where the row at date t is decided using information up to the close
  of t ONLY.
- The engine shifts weights by one day (no lookahead, #3): the weight
  decided at close t earns returns from t+1.
- Costs (#2) are charged on weight changes at the estimated per-side
  cost from src/backtest/costs.py.

v0 simplifications, documented deliberately:
- Execution is approximated at the close of t+1 via close-to-close
  returns; intra-period weight drift is not modeled for turnover.
- Weights are treated as long-only or long-short fractions of NAV;
  no borrowing costs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.backtest import costs as costs_mod


@dataclass
class BacktestResult:
    net_returns: pd.Series
    gross_returns: pd.Series
    costs: pd.Series
    turnover: pd.Series          # one-way, Σ|Δw| per day
    exposure: pd.Series          # Σw per day (executed)
    executed_weights: pd.DataFrame

    def annual_turnover(self) -> float:
        return float(self.turnover.mean() * 252)

    def avg_exposure(self) -> float:
        return float(self.exposure.mean())


def run_backtest(weights: pd.DataFrame, prices: pd.DataFrame) -> BacktestResult:
    """Run target weights through execution and costs.

    weights: dates × tickers, decided at the close of each date.
    prices:  MultiIndex-column panel (field × ticker) with Close and
             Volume for at least the weight tickers.
    """
    closes = prices["Close"][weights.columns]
    volume = prices["Volume"][weights.columns]

    if (weights.fillna(0.0).sum(axis=1) > 1.0 + 1e-9).any():
        raise ValueError("weight rows must sum to ≤ 1.0")

    # No lookahead: weight decided at close t is held during day t+1.
    executed = weights.reindex(closes.index).shift(1).fillna(0.0)

    rets = closes.pct_change().fillna(0.0)
    gross = (executed * rets).sum(axis=1)

    adv = (closes * volume).mean()
    per_side = costs_mod.cost_per_side(adv)
    cost = costs_mod.transaction_costs(executed, per_side)

    net = gross - cost
    turnover = executed.diff().abs().sum(axis=1)
    if len(turnover):
        turnover.iloc[0] = executed.iloc[0].abs().sum()

    return BacktestResult(
        net_returns=net,
        gross_returns=gross,
        costs=cost,
        turnover=turnover,
        exposure=executed.sum(axis=1),
        executed_weights=executed,
    )
