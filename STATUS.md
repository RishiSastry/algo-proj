# STATUS — AI-infra systematic trading

*Auto-generated 2026-09-24 by `scripts/status.py` (nightly via cron). Last price bar: 2026-09-24.*

## Signal

**IN — uptrend** · basket index is +29.3% vs its 210d MA · state unchanged since 2025-05-13.

The strategy: hold the equal-weight basket while its index is above the 210-day MA (month-end check, next-day execution); cash otherwise.

## Paper books (started 2026-09-15, $1K each)

| book | holds | NAV | total return |
|---|---|---|---|
| slices16 | 16 S&P names via Stock Slices (Phase-1 candidate) | $1,100.34 | +10.0% |
| basket | 27 names, fractional (ideal) | $1,087.62 | +8.8% |
| smh | 1 whole-share ETF (fallback) | $1,060.71 | +6.1% |

Benchmarks since inception: SPY buy&hold +0.8%, SMH buy&hold +10.9%.

## Ops

Last daily-log entry: `| 2026-09-24 | 2026-09-24 | 18.5% | 126.4% | clean |`

- Cron: weekdays 18:30 — data refresh, integrity, paper trade, status.
- Missed runs self-heal via catch-up; integrity flags missing bars.
- Incidents: see `research/2026-09-24-data-incident.md` (resolved).

## Pending decisions (Rishi)

- AMZN in or out of the tradable sleeve (48% locked exposure at MS).
- Phase-1 go/no-go: after ~4+ weeks of paper, if books track expectations → $1K live in Schwab via Stock Slices (slices16).
- Phase-2 gate (months out): sizing, hedge-vs-sleeve use of the signal, sector diversification, options overlay.
