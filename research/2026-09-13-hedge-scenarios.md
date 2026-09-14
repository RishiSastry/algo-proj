# Hedge scenario mocks — trimming AMZN / shorting the basket

**Status: scenario measurement on a frozen portfolio replay. Not a
walk-forward-validated strategy, and not a recommendation — the
decisions here (selling employer stock, opening shorts) are personal
and discretionary, outside this repo's mandate. The lab's job was to
size the effects honestly.**

## Question (Rishi's): sell $5K of the locked AMZN, short the basket with it?

Design holes filled before running:
1. **Vehicle:** short SMH (practically shortable); idealized EW-basket
   short included for comparison — at this size the difference is nil.
2. **Timing:** always-on vs gated by the validated trend signal
   (short only when the basket is below its 210d MA — 26% of days,
   30 round trips in 21 years).
3. **Mechanics:** a short needs margin, not cash — the AMZN sale and
   the short are independent levers, so they are simulated separately
   and together.
4. **Sizing:** fixed $5K turns out to be a mis-specification — it
   shrinks to noise as the book compounds. Maintained-percentage
   hedges (5.4% ≈ $5K today; 21.7% ≈ $20K today) are the meaningful
   version.
5. **Scoring:** total wealth (locked AMZN + Schwab book + hedge),
   replayed 2006–2026 and 2016–2026. Core book = today's mix,
   buy-and-hold drift; VT proxied by SPY; CRWV/SPCX/SOUN proxied by
   the EW basket. Costs: 10 bps/side, 0.5%/yr borrow while short.

## Results (total wealth, 2006–2026)

|                        | CAGR | vol | Sharpe | maxDD | worst yr |
|------------------------|------|-----|--------|-------|----------|
| A hold everything      | 29.8% | 32.4% | 0.97 | -66.9% | -52.3% |
| B sell $5K AMZN → cash | 29.7% | 31.7% | 0.98 | -65.2% | -51.3% |
| C B + gated $5K short  | 29.7% | 31.5% | 0.98 | -63.9% | -50.4% |
| P1 gated 5.4% maintained | 29.8% | 31.9% | 0.98 | -65.5% | -50.8% |
| P2 ALWAYS 5.4% maintained | 28.8% | 31.2% | 0.97 | -65.1% | -50.5% |
| P3 gated 21.7% maintained | 29.4% | 30.6% | 1.00 | -61.1% | -46.1% |

(2016–2026 window: same ordering; always-on costs 2 CAGR points there.)

## What the numbers teach

1. **$5K of anything is a rounding error against this book.** The
   proposed trade (C) improves max drawdown by 3 points out of 67.
   The portfolio's fate is set by the ~68% AMZN+NVDA core, which no
   small overlay can touch.
2. **The gate earns its keep.** Maintained always-on shorting (P2)
   pays ~1–2 CAGR points for barely more protection than the gated
   version (P1); the trend signal spends the short only when it has
   historically mattered.
3. **Sizing is the real lever.** A gated ~20% hedge (P3) buys 6 points
   of max drawdown and 6 points of worst-year for 0.4 CAGR — the best
   risk trade on the board. And even it leaves a -61% drawdown.
4. **Therefore: hedging cannot substitute for the core decision.** How
   much AMZN/NVDA to hold is a tax-, employment-, and life-constrained
   personal decision; no overlay in this lab changes that math.
5. Selling $5K AMZN (B) does roughly as much as the $5K short (C) —
   with no margin account, no borrow fees, no basis risk.

## How this could be fooling us

- **Basis risk is understated:** SMH holds no AMZN. The hedge only
  fires when the *sector* trends down; an idiosyncratic AMZN drop
  (guidance miss, AWS stumble) goes unhedged. 2008/2022 were broad, so
  the replay flatters the cross-hedge.
- **The trend signal was validated as a long on/off switch, not a
  short trigger.** Using it to time a hedge is a new, untested use —
  plausible, but its OOS record is inherited, not earned.
- **Frozen composition:** no contributions, no vesting of more AMZN
  (which, if ongoing, worsens concentration each quarter), no
  rebalancing, dividends via adjusted closes only.
- Same survivorship/hindsight caveats as every note; borrow fees in
  stress can exceed 0.5%/yr precisely when the hedge is on.
- Practical frictions not modeled: Schwab margin approval, employer
  trading windows on the MS account, capital-gains tax on any AMZN
  sale (lot-dependent), and the standing mandate that the MS account
  is untouched — trimming AMZN would require Rishi to revise that
  mandate explicitly.
