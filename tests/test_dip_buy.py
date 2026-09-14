import numpy as np
import pandas as pd
import pytest

from src.strategies.dip_buy import dip_signal


def make_index(moves: list[float], base: float = 100.0) -> pd.Series:
    dates = pd.bdate_range("2020-01-01", periods=len(moves))
    return pd.Series(base * np.cumprod(1 + np.array(moves)), index=dates)


def test_dip_in_uptrend_triggers_hold():
    # long steady rise (gate up), then a -7.8% two-day dip, then flat
    moves = [0.004] * 300 + [-0.04, -0.04] + [0.0] * 30
    idx = make_index(moves)
    sig = dip_signal(idx, dip_window=5, threshold=-0.05, hold_days=10, ma_window=200)
    assert sig.iloc[301] == 1.0             # trigger day
    assert sig.iloc[302:311].eq(1.0).all()  # held (re-triggers may extend)
    assert sig.iloc[320] == 0.0             # expired well after last hold


def test_no_trigger_without_gate():
    # falling market: dips galore but gate is down -> never on
    moves = [-0.004] * 300 + [-0.03, -0.03] + [0.0] * 10
    idx = make_index(moves)
    sig = dip_signal(idx, ma_window=200)
    assert sig.sum() == 0.0


def test_gate_break_forces_exit():
    # dip triggers, then keeps falling through the MA -> exit before hold ends
    moves = [0.004] * 300 + [-0.05, -0.05, -0.05, -0.05, -0.05, -0.05] + [0.0] * 10
    idx = make_index(moves)
    sig = dip_signal(idx, dip_window=5, threshold=-0.05, hold_days=21, ma_window=200)
    on_days = sig[sig == 1.0]
    assert len(on_days) > 0              # it did trigger
    below = idx < idx.rolling(200).mean()
    assert (sig[below] == 0.0).all()     # never on while below the MA


def test_retrigger_restarts_clock():
    moves = [0.004] * 300 + [-0.03, -0.03] + [0.002] * 5 + [-0.03, -0.03] + [0.002] * 20
    idx = make_index(moves)
    sig = dip_signal(idx, dip_window=5, threshold=-0.05, hold_days=10, ma_window=200)
    second_trigger = 308  # second dip pair ends here
    assert sig.iloc[second_trigger : second_trigger + 10].eq(1.0).all()
