# Trade journal

Phase 1 gate (plan.md): 20–30 journaled trades with the system followed
on every one. Every trade gets a row in `trades.csv` at entry and is
completed at exit. The point is process, not P&L.

Rules:
- The row is written **before or at entry**, never reconstructed later.
- `rule` must name a strategy file + the specific rule that fired. If
  no rule fired, the trade does not happen (CLAUDE.md #1).
- `planned_exit` is written at entry and is binding. If the actual exit
  differs, `followed_system` = N and `notes` explains why.
- Review the journal at each session start; count `followed_system` = Y
  toward the Phase 1 gate.

## trades.csv columns

| column | meaning |
|---|---|
| id | sequential trade id |
| entry_date / exit_date | ISO dates (exit blank while open) |
| ticker | universe ticker |
| direction | long / short |
| size_usd | dollar notional at entry |
| entry_px / exit_px | fill prices |
| rule | e.g. `momentum_xs: top-third month-end rebalance` |
| planned_exit | the exit rule as written at entry |
| followed_system | Y/N — filled at exit |
| mood | one word at entry (calm / fomo / anxious / bored …) |
| notes | anything the numbers don't capture |
