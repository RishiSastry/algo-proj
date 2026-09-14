# Pre-registration: dip-buying in uptrends (strategy family #2)

**This note is committed BEFORE any backtest of this family is run.**
Everything below — rule, defaults, grid, protocol, and the survival
criterion — is fixed now. If the results section (appended later)
shows anything other than what the criterion demands, the family is
killed. No post-hoc variants.

## Hypothesis

Within an established uptrend, sharp multi-day selloffs in the AI-infra
basket are, on average, overreactions that partially revert over the
following days. Mechanism: forced/emotional selling in a high-beta
herd snaps back when the regime is intact. This is a different
mechanism (short-horizon mean reversion) and horizon (days) from the
trend sleeve (regime following, months).

## Rule (v0 defaults, chosen before testing)

- **Regime gate:** basket index above its 210d MA at the close
  (evaluated daily — same MA as the trend sleeve).
- **Trigger:** basket 5-day simple return ≤ **-5%** while the gate is up.
- **Position:** 100% of the sleeve into the EW basket at the next
  day's execution (engine's standard t+1 shift). Otherwise cash.
- **Exit:** after **10 trading days**; a re-trigger during the hold
  restarts the clock; the gate turning down forces immediate exit.
- Costs and eligibility rules identical to every other strategy.

## Evaluation protocol

1. Full-sample run with costs (in-sample, labeled as such).
2. Sensitivity surface, 27 cells: dip window {3,5,10}d × threshold
   {-3%,-5%,-7%} × hold {5,10,21}d. Diagnostics only.
3. Walk-forward over that same grid: train 756d, test 126d, select by
   train Sharpe (identical protocol to the momentum and trend runs).
4. Conditional-mean diagnostic: average next-10-day basket return
   after triggers vs unconditionally, with a t-stat.

## Survival criterion (fixed now)

The sleeve gets a paper book only if **walk-forward OOS net Sharpe
exceeds the EW basket's Sharpe over the identical OOS window.**
Rationale: an intermittent long-basket sleeve with no timing skill
converges to a diluted copy of the basket; beating the basket's own
Sharpe is the minimum evidence the *timing* adds information.
Anything less → killed, results recorded, no iteration.

Snoop-ledger note: this is the 4th strategy family tested against this
sample (~140 prior backtests). One pre-registered shot; no rescues.

---

# Results (appended 2026-09-13, after the pre-registered run)

## Verdict: FAILED the survival criterion — family killed.

- **Walk-forward OOS net Sharpe: +0.53 vs EW basket +1.03** over the
  identical 2008–2026 window (SPY: +0.64). Not close.
- Default cell in-sample: 7.4% CAGR, Sharpe 0.57, 12.8% average
  exposure, ~5× turnover.
- Surface (27 cells): 0.23–0.85, best cells are the *mildest* dips
  with the *longest* holds — i.e., the family scores best as it
  degenerates toward "just own the basket," the same convergence
  pattern that unmasked PEAD. Walk-forward selection scattered across
  7 cells with no persistence.
- Conditional-mean diagnostic: post-dip days do average double the
  unconditional daily return (0.24% vs 0.12%/day) — but t = 1.28,
  p = 0.20 on 699 active days. Indistinguishable from luck. There is
  a hint of an effect; there is not evidence of one.

## Read

The dip-buy edge, if it exists, is too weak and too infrequent to
survive costs and estimation noise at this universe's size. Per the
pre-registration: killed, no variants, no rescues. The snoop ledger
gains 28 runs (~168 total).

## How this could be fooling us

- The conditional mean IS elevated — with 3× more history or a wider
  cross-section of sectors, this exact rule might clear significance.
  "Killed here" means killed *on this universe with this sample*, not
  disproven as a market phenomenon.
- The survival criterion (beat the basket's Sharpe) is strict for a
  12.8%-exposure sleeve; a blend-level criterion could have passed a
  weak-positive sleeve. That laxer bar was considered and rejected at
  pre-registration precisely because it rescues everything.
