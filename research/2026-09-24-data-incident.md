# Incident: vendor outage 2026-09-21 poisoned the price cache

First real operational incident, surfaced by 11 days of unattended
running. Timeline and fixes, for the record.

## What happened

- **2026-09-18 (Fri):** cron did not run (machine likely asleep). By
  design the catch-up loop absorbed this on Monday. Not a bug.
- **2026-09-21 (Mon):** the 18:30 cron fetched the day's bars during a
  yfinance outage. The vendor returned rows with **real volume but NaN
  prices** for 28 of 29 tickers. The cache stored them and — worse —
  marked the range covered, so no later run would ever re-fetch it.
- **Consequences:** the smh paper book crashed nightly from 9/21 on
  (`int(NaN)` on the whole-share sizing path), freezing it at 9/18;
  the crash aborted the script before the slices16 book's turn,
  freezing it at 9/17 with no error of its own. The basket book
  sailed through with a blank NAV mark on 9/21 (ledger row kept as-is
  — ledgers are records). The EW benchmark YTD was silently understated
  (112% vs the true 126%). The nightly integrity check reported
  **clean** throughout: a single missing bar evaded all three rules
  (bad prices, >5-day gaps, >50% moves).

## Fixes (all committed today)

1. `_download` drops any bar without a Close — a bar without a close
   is not a bar (catches all-NaN and volume-only shapes).
2. An empty tail fetch no longer extends the cache's covered range —
   outage days are retried on the next run instead of being declared
   covered. (Holidays cost one harmless re-probe.)
3. The simulator defers fills when the open is NaN (retry next day)
   instead of crashing, and NAV marks use last-known closes.
4. Buy sizing is net of transaction cost (fixes cash drifting to
   -$1.11 in the basket book).
5. `daily_update` now flags missing bars — the exact signature this
   incident produced. Had it existed on 9/21, the log would have
   screamed instead of saying "clean".
6. Cache rows for 9/21 repaired from a fresh fetch for all 28 tickers.

## Lessons

- **Silent failure is the enemy, not failure.** The crash (smh) was
  the *good* outcome — it froze state loudly. The books that "worked"
  through bad data were the dangerous ones.
- A cache that can never re-fetch is a cache that can never heal;
  coverage metadata must only assert what was actually received.
- Monitoring must alarm on *absence* (missing bars), not just on
  *wrongness* (bad values). Absence is what vendors actually deliver
  when they break.
- Paper trading is doing its job: every one of these would have been
  a real-money incident in Phase 1.

## Book status after repair (all through 2026-09-24, signal IN)

| book | NAV | since 9/15 open |
|---|---|---|
| basket (27, fractional) | $1,087.62 | +8.8% |
| slices16 (16, Slices) | $1,100.34 | +10.0% |
| smh (1 ETF, whole shares) | $1,060.71 | +6.1% |
