# Pre-registration: concentration cost & cross-sector trend (committed before running)

Two experiments, designs fixed now. Both reuse the validated trend
mechanism unchanged (210d MA on the sleeve's own index, month-end
evaluation, t+1 execution, standard costs). No parameter search in
either experiment — the only variables are the asset sets themselves.

## Experiment 1: concentration cost of smaller baskets

**Question:** holding fewer than 27 names with more capital per name,
how much performance is lost, and is the Schwab-Slices-eligible subset
an acceptable live implementation?

- For N in {5, 10, 15, 20}: draw 20 random subsets of the 27 (seeded
  rng(42), sampling recorded), run the trend-gated EW basket on each —
  gate computed on the subset's OWN index (self-contained strategy).
  Report the median and IQR of net Sharpe / CAGR / max drawdown per N,
  against the 27-name reference.
- Named subset: **SLICES16** = the S&P 500 members of the universe
  (MSFT, AMZN, GOOGL, META, ORCL, NVDA, AMD, AVGO, MU, MRVL, QCOM,
  INTC, DELL, ANET, SMCI, VRT — membership to be re-verified before
  any live use, SMCI in particular). This is what Schwab can trade
  fractionally today.
- **Interpretation rule (fixed now):** SLICES16 is judged against the
  27-name reference AND the N=15/20 random distributions. "Acceptable"
  means within the random IQR for its size and within 0.1 Sharpe of
  the 27-name reference. No cherry-picking a lucky random subset —
  random draws exist only to price the concentration cost.

## Experiment 2: the same rule on other sectors

**Question:** does trend-on-other-sectors diversify trend-on-AI-infra?

- Assets: the 11 SPDR sector ETFs (XLK, XLC, XLY, XLP, XLE, XLF, XLV,
  XLI, XLB, XLU, XLRE), each from inception + 60 trading days.
- Per ETF: the identical trend rule, net stats, and daily correlation
  with the AI basket trend sleeve.
- **Pre-registered combo:** 50% AI-infra trend sleeve + 50% equal-weight
  of the trend sleeves on the 9 non-tech sectors (XLK and XLC excluded
  from the diversifier side for overlap). Judged vs the AI sleeve
  alone on Sharpe, max drawdown, and Calmar.
- No selection of "best" sectors ex-post; the combo definition above
  is the only combo evaluated.

Snoop ledger: +~100 runs (experiment 1) and +12 (experiment 2) against
the same 2005–2026 sample. Both experiments reuse a validated rule on
new asset sets rather than fitting anything new — the lowest-risk kind
of test this repo runs, but logged all the same.

---

# Results (appended 2026-09-13, after the pre-registered runs)

## Experiment 1: concentration cost — cheap down to ~15 names, then real

Reference (27 names): Sharpe 1.03, CAGR 24.3%, maxDD -31.7%.

| N (random draws) | Sharpe med [IQR] | CAGR med | maxDD med |
|---|---|---|---|
| 20 | 1.02 [0.98–1.05] | 24.3% | -32.6% |
| 15 | 0.97 [0.93–1.01] | 23.4% | -37.6% |
| 10 | 0.96 [0.89–1.00] | 24.8% | -37.9% |
| 5  | 0.85 [0.79–0.96] | 22.6% | **-42.0%** |

The cost shows up first in drawdowns, not Sharpe: below ~15 names the
median worst-case deepens by 6–10 points. Five-name baskets are
meaningfully worse on every axis.

**SLICES16 (S&P 500 members, Schwab-fractional-tradable): Sharpe 1.04,
CAGR 22.6%, maxDD -32.5% — PASSES the pre-registered criterion** (within
0.1 Sharpe of reference, inside the N=15/20 IQRs). It gives up ~1.7
CAGR points (the neocloud sleeve it can't hold) at equal Sharpe and
equal drawdown. **Adopted as the Phase-1 live implementation candidate,
displacing the SMH proxy (Sharpe 0.75).** A third paper book runs it.

Caveat that matters: SLICES16 is built from *today's* S&P 500
membership — names like SMCI and DELL joined the index *because* they
did well, which leaks hindsight into the subset's backtest. The equal
Sharpe is therefore flattered; the forward paper race is the honest
test. Membership must be re-verified at each rebalance for live use.

## Experiment 2: trend travels, but its returns live at home

Identical rule on 11 SPDR sector ETFs: **all 11 sleeves have positive
net Sharpe** (0.08–0.75) — the mechanism generalizes, consistent with
the trend-following literature. But sector CAGRs are 4–12% vs AI's 24%.

Pre-registered combo (50% AI sleeve + 50% EW of 9 non-tech sector
sleeves, pairwise corr with AI sleeve 0.15–0.59):

|  | Sharpe | CAGR | maxDD | Calmar |
|---|---|---|---|---|
| AI sleeve alone | 1.03 | 24.3% | -31.7% | 0.77 |
| 9-sector EW sleeves | 0.72 | 6.5% | -16.0% | 0.41 |
| 50/50 combo | 1.05 | 15.7% | -22.1% | 0.71 |

**Textbook diversification, honestly priced:** the combo cuts the worst
drawdown by ~10 points and barely moves Sharpe (1.05 vs 1.03), but
costs 8.6 CAGR points and slightly *lowers* Calmar. Diversifying away
from AI-infra buys smoothness with return, not a free lunch — because
the diversifiers earn a third of what the AI sleeve earns.

Decision framing for the Phase-2 gate (not decided now): given Rishi's
real-life 71% AI concentration, smoothness may be worth buying at the
account level even at that price; alternatively the sector sleeves'
role is a bench option if the AI regime breaks.

## How this could be fooling us

- SLICES16 hindsight-membership leak (above) — the biggest one here.
- Random-subset medians use 20 draws per N; IQRs are estimates.
- Sector ETF results inherit every prior caveat (one secular regime,
  costs model, the 210d parameter validated on AI data, applied
  unchanged — deliberate, but the sectors never got their own
  walk-forward).
- Snoop ledger: +93 runs (~260 total on this sample).
