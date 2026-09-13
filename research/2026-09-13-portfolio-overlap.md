# Portfolio overlap with the AI-infra universe

**Data:** Schwab positions export 2026-09-13 (8 lines incl. cash,
total ≈ $48K). Raw dollars live in `portfolio/holdings.csv`
(gitignored); this note reports proportions. ETF look-through via
yfinance top-10 holdings with share-class/foreign-listing aliases
(GOOG→GOOGL, 2330.TW→TSM).

## Result: the portfolio already IS an AI-infra book

| exposure | % of portfolio | via |
|---|---|---|
| NVDA | **38.4%** | direct (37.5%) + VT look-through |
| CRWV | 3.1% | direct |
| GOOGL, MSFT, AMZN, AVGO, TSM, META | ~2.7% combined | VT top-10 look-through |
| **Universe total (lower bound)** | **44.1%** | |

Lower bound: the top-10 look-through resolves only ~21% of VT; the
remaining ~79% certainly holds more universe names (ASML, AMD, QCOM,
INTC, MU, ORCL, ANET, DELL…), each individually small — realistically
another ~1% of portfolio. Cash is 4.4%. SPCX (SpaceX fund) and SOUN
are AI-adjacent but outside the universe definition; BRK-B and AAPL
are the only meaningful non-AI-infra equity exposure.

## Implications for the program

1. **NVDA is the portfolio.** One name at 38% dwarfs every decision
   this project will make. The factor note applies directly: in a
   sector drawdown (PC1 > 0.7 regimes), NVDA, CRWV, VT's tech sleeve,
   and any strategy on this universe all fall together.
2. **The trend sleeve's value here is its drawdown behavior, not its
   return.** Adding a $1K (2% of portfolio) sleeve changes nothing
   materially; but the *signal itself* — basket index vs 210d MA — is
   now monitoring a factor the portfolio is 44%+ exposed to. The daily
   cron prints that signal state; it is arguably the most useful
   output of the whole system for this portfolio.
3. **Phase-2 sizing context:** a "sliver" of ≈$48K is $2–5K. At that
   size the whole-share basket still doesn't work (needs ~$45K+ per
   the assembly note); the Schwab expression remains the SMH proxy —
   which would *add* to the 44% concentration, not diversify it.
   Worth an explicit discussion at the gate review: the honest use of
   the validated signal might be de-risking the existing book in
   downtrends rather than adding a new long sleeve on top.

## How this could be fooling us

- **Top-10 look-through is a floor**, single-vendor, single snapshot;
  ETF weights drift daily.
- **One account:** if other accounts exist (401k, IRA), the true
  overlap could differ; this covers the Schwab individual account only.
- **Universe definition:** AAPL sits outside our universe by choice;
  by a looser "big tech" definition the concentration is higher still.
- No action is recommended here on the existing holdings — that is a
  discretionary portfolio decision, explicitly out of this project's
  mandate (CLAUDE.md #1). The numbers are recorded so the Phase-2 gate
  is made with eyes open.
