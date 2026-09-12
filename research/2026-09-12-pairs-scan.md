# Pairs scan — no tradable cointegration in the universe

**Status: finding (the test IS train/test split; the negative is OOS-confirmed).**

## Protocol (pre-registered)

- Candidates: within-bucket pairs where both names have ≥ 5 years of
  joint history before 2018-01-01 → **46 pairs** (10 hyperscaler, 36
  chip; hardware yielded 1, neoclouds 0 — histories too short).
- Train (joint start → 2017-12): Engle-Granger cointegration on log
  prices, **Bonferroni-corrected**: pass requires p < 0.05/46 ≈ 0.0011.
- Test (2018-01 → 2026-09): hedge ratio frozen from train, ADF on the
  out-of-sample spread.
- Full table: `figures/pairs-scan.csv`.

## Result: zero survivors

Best train pair: GOOGL/MSFT at p = 0.003 — 3× the corrected threshold,
and its OOS spread is non-stationary anyway (ADF p = 0.17).

The multiple-testing correction earned its keep: at a naive α = 0.05,
three pairs (GOOGL/MSFT, ASML/TSM, GOOGL/META) would have been
"discoveries" — **all three fail the OOS stationarity check** (p =
0.17, 0.77, 0.86). Uncorrected scanning would have shipped three fake
strategies. That is the whole argument for the protocol in one row of
a CSV.

Economically this is unsurprising in hindsight: these firms share a
sector factor but have wildly different business models and idiosyncratic
arcs (INTC's decline, AMD's resurrection, META's pivots). A common
factor produces correlation, not cointegration.

**Decision: no pairs strategy on this universe. Killed before a single
backtest was run on it** — the scan cost 46 statistical tests, zero
strategy-fitting degrees of freedom.

## How this could be fooling us

- **Engle-Granger is one test** (linear, constant hedge ratio). Time-
  varying-beta (Kalman) or nonlinear relationships were not tested —
  deliberately, because each adds a forest of researcher degrees of
  freedom that this sample can't support.
- **The 2018 split is a single choice**; a different split shifts
  p-values. With zero pairs anywhere near the threshold, the
  conclusion is unlikely to be split-sensitive.
- **Bonferroni is conservative**; a true weak cointegration could be
  buried. But "too weak to clear a 46-test correction" and "tradable
  after costs" don't overlap much in practice.
- **Short-history names excluded:** neocloud pairs (e.g. miners with
  similar pivots) were untestable. Revisit when they have ≥ 5 years of
  post-pivot data — noted for ~2027+.
