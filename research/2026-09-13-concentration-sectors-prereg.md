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
