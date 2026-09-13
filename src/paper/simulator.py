"""Broker-independent paper-trading simulator.

Why this exists: Schwab's Trader API has no paper sandbox (paperMoney
is thinkorswim-only), and CLAUDE.md forbids live orders until the plan
says otherwise. So the paper phase runs here, against real cached
prices, with the same discipline as the backtest engine:

- A target decided after the close of day t is EXECUTED at the open of
  the next trading day (never same-day).
- Costs: flat 10 bps per side (5 bps slippage + ~5 bps spread), the
  same order of magnitude as the engine's ladder.
- Optional whole-share constraint (Schwab has no fractional shares
  outside S&P 500 Stock Slices).

State is a JSON file per account; every fill and daily NAV mark is
appended to a CSV ledger. Runs are idempotent per trading day.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

COST_PER_SIDE = 0.0010  # 10 bps
STARTING_CASH = 1_000.0


@dataclass
class Account:
    root: Path                     # directory holding state.json + ledger.csv
    whole_shares: bool = False
    cash: float = STARTING_CASH
    positions: dict = field(default_factory=dict)   # ticker -> shares
    pending: dict = field(default_factory=dict)     # ticker -> target weight
    last_processed: str = ""                        # ISO date of last bar seen

    @property
    def state_path(self) -> Path:
        return self.root / "state.json"

    @property
    def ledger_path(self) -> Path:
        return self.root / "ledger.csv"

    @classmethod
    def load(cls, root: Path, whole_shares: bool = False) -> "Account":
        acct = cls(root=root, whole_shares=whole_shares)
        if acct.state_path.exists():
            raw = json.loads(acct.state_path.read_text())
            acct.cash = raw["cash"]
            acct.positions = raw["positions"]
            acct.pending = raw["pending"]
            acct.last_processed = raw["last_processed"]
        return acct

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps({
            "cash": self.cash,
            "positions": self.positions,
            "pending": self.pending,
            "last_processed": self.last_processed,
        }, indent=2))

    def _append_ledger(self, rows: list[dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(rows)
        header = not self.ledger_path.exists()
        frame.to_csv(self.ledger_path, mode="a", header=header, index=False)

    def nav(self, closes: pd.Series) -> float:
        value = self.cash
        for t, sh in self.positions.items():
            value += sh * float(closes[t])
        return value

    def process_day(self, date: pd.Timestamp, opens: pd.Series,
                    closes: pd.Series, new_targets: dict[str, float]) -> bool:
        """One trading day: execute yesterday's pending targets at
        today's open, mark NAV at today's close, queue new targets for
        tomorrow. Returns False if this bar was already processed."""
        day = str(pd.Timestamp(date).date())
        if self.last_processed >= day:
            return False

        rows = []
        if self.pending:
            nav_open = self.cash + sum(
                sh * float(opens[t]) for t, sh in self.positions.items())
            for ticker, target_w in self.pending.items():
                px = float(opens[ticker])
                have = self.positions.get(ticker, 0.0)
                want = target_w * nav_open / px
                if self.whole_shares:
                    want = float(int(want))  # floor toward zero
                delta = want - have
                if abs(delta * px) < 1.0:  # ignore sub-$1 rebalances
                    continue
                cost = abs(delta) * px * COST_PER_SIDE
                self.cash -= delta * px + cost
                self.positions[ticker] = want
                if want == 0.0:
                    del self.positions[ticker]
                rows.append({"date": day, "event": "FILL", "ticker": ticker,
                             "shares": round(delta, 4), "price": round(px, 4),
                             "value": round(delta * px, 2), "cost": round(cost, 4)})
            self.pending = {}

        nav = self.nav(closes)
        rows.append({"date": day, "event": "MARK", "ticker": "",
                     "shares": "", "price": "", "value": round(nav, 2), "cost": ""})
        self._append_ledger(rows)

        # queue tomorrow's targets: only tickers whose target differs
        # meaningfully from the current weight
        for ticker, w in new_targets.items():
            held = self.positions.get(ticker, 0.0) * float(closes[ticker]) / nav
            if abs(w - held) > 0.005:
                self.pending[ticker] = w
        # explicit exits for held names absent from the target
        for ticker in list(self.positions):
            if ticker not in new_targets:
                self.pending[ticker] = 0.0

        self.last_processed = day
        self.save()
        return True
