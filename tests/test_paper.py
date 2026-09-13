import pandas as pd
import pytest

from src.paper.simulator import Account, COST_PER_SIDE


@pytest.fixture
def acct(tmp_path):
    return Account.load(tmp_path / "test", whole_shares=False)


def series(**kv):
    return pd.Series(kv)


def test_target_fills_next_day_not_same_day(acct):
    d1, d2 = pd.Timestamp("2026-01-05"), pd.Timestamp("2026-01-06")
    acct.process_day(d1, series(SMH=100.0), series(SMH=102.0), {"SMH": 1.0})
    assert acct.positions == {}          # nothing filled on signal day
    assert acct.pending == {"SMH": 1.0}

    acct.process_day(d2, series(SMH=101.0), series(SMH=103.0), {"SMH": 1.0})
    assert acct.positions["SMH"] > 0     # filled at d2 open
    fills = pd.read_csv(acct.ledger_path)
    fill = fills[fills["event"] == "FILL"].iloc[0]
    assert fill["price"] == pytest.approx(101.0)


def test_whole_shares_floor(tmp_path):
    acct = Account.load(tmp_path / "ws", whole_shares=True)
    acct.process_day(pd.Timestamp("2026-01-05"), series(SMH=300.0),
                     series(SMH=300.0), {"SMH": 1.0})
    acct.process_day(pd.Timestamp("2026-01-06"), series(SMH=300.0),
                     series(SMH=300.0), {"SMH": 1.0})
    assert acct.positions["SMH"] == 3.0  # floor(1000/300), not 3.33
    assert acct.cash > 0


def test_idempotent_per_day(acct):
    d = pd.Timestamp("2026-01-05")
    assert acct.process_day(d, series(SMH=100.0), series(SMH=100.0), {"SMH": 1.0})
    assert not acct.process_day(d, series(SMH=100.0), series(SMH=100.0), {"SMH": 1.0})
    marks = pd.read_csv(acct.ledger_path)
    assert (marks["event"] == "MARK").sum() == 1


def test_exit_queued_when_target_drops(acct):
    days = pd.bdate_range("2026-01-05", periods=3)
    acct.process_day(days[0], series(SMH=100.0), series(SMH=100.0), {"SMH": 1.0})
    acct.process_day(days[1], series(SMH=100.0), series(SMH=100.0), {"SMH": 1.0})
    assert acct.positions["SMH"] > 0
    acct.process_day(days[2], series(SMH=100.0), series(SMH=100.0), {})  # signal off
    assert acct.pending == {"SMH": 0.0}


def test_costs_charged_on_fill(acct):
    acct.process_day(pd.Timestamp("2026-01-05"), series(SMH=100.0),
                     series(SMH=100.0), {"SMH": 1.0})
    acct.process_day(pd.Timestamp("2026-01-06"), series(SMH=100.0),
                     series(SMH=100.0), {"SMH": 1.0})
    fills = pd.read_csv(acct.ledger_path)
    fill = fills[fills["event"] == "FILL"].iloc[0]
    assert fill["cost"] == pytest.approx(abs(fill["value"]) * COST_PER_SIDE, rel=1e-6)


def test_state_roundtrip(tmp_path):
    root = tmp_path / "rt"
    acct = Account.load(root)
    acct.process_day(pd.Timestamp("2026-01-05"), series(SMH=100.0),
                     series(SMH=100.0), {"SMH": 1.0})
    reloaded = Account.load(root)
    assert reloaded.pending == {"SMH": 1.0}
    assert reloaded.last_processed == "2026-01-05"
