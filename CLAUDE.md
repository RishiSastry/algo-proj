# CLAUDE.md — AI-Infrastructure Systematic Trading Research

## What this repo is
A research codebase for developing, backtesting, and paper-trading **systematic** strategies on a fixed universe of AI-infrastructure equities (hyperscalers, neoclouds, chipmakers, and supporting hardware). Owner: Rishi. Purpose is learning quant research methodology and building a validated strategy — not discretionary trading, not HFT.

## Non-negotiable principles
1. **No discretionary trades in code.** Every entry/exit is a rule. If a decision needs a human opinion, it is not a strategy — it's a parameter, and it gets documented.
2. **Every backtest models costs.** Default assumptions: 5 bps slippage per side + half the bid-ask spread. Never report a result without costs applied.
3. **No lookahead.** Signals computed at close of day `t` may only trade at open of `t+1` or later. Use `.shift(1)` on signals and add a test that asserts it.
4. **Survivorship bias is explicit.** The universe file records IPO date per ticker. Backtests may only include a ticker after its IPO date + 60 trading days.
5. **Two benchmarks, always.** Every strategy reports against (a) buy-and-hold SPY and (b) an equal-weight buy-and-hold of the universe. Beating SPY but losing to (b) means the strategy added nothing.
6. **Walk-forward before conclusions.** In-sample results are hypotheses. Only walk-forward / out-of-sample results are reported as findings.
7. **Report the sin list.** Every research note ends with a "How this could be fooling us" section: overfitting, lookahead, survivorship, data snooping, regime dependence.

## Stack
- Python 3.12, managed with `uv`
- pandas, numpy, matplotlib, scipy, statsmodels
- Data: `yfinance` (daily OHLCV, adjusted). Cache everything to Parquet under `data/cache/`. Never re-download what's cached.
- Backtesting: hand-rolled vectorized pandas in `src/backtest/` (no framework until we understand every assumption). Revisit `vectorbt` later.
- Tests: `pytest`. Data-integrity and no-lookahead tests are mandatory.
- Notebooks are for exploration only. Anything reused moves into `src/`.

## Layout
```
pyproject.toml
CLAUDE.md
plan.md
universe/universe.csv        # ticker, name, bucket, ipo_date, notes
data/cache/                  # parquet, gitignored
src/
  data/      fetch.py, cache.py, integrity.py
  analysis/  returns.py, stats.py, factor.py
  backtest/  engine.py, costs.py, metrics.py
  strategies/ momentum_xs.py, ...
research/    dated markdown notes: YYYY-MM-DD-<topic>.md
notebooks/
tests/
```

## Conventions
- Returns: use log returns for analysis, simple returns for P&L.
- Prices: adjusted close for signals; log which adjustment source was used.
- Dates: tz-naive, US market calendar. Drop non-trading days explicitly.
- Every strategy exposes `generate_weights(prices: DataFrame) -> DataFrame` (dates × tickers, rows sum to ≤ 1.0). The engine handles execution, costs, and metrics — strategies only produce weights.
- Metrics reported: CAGR, annualized vol, Sharpe, Sortino, max drawdown, Calmar, turnover, exposure, hit rate. Always vs. both benchmarks.
- Plots saved to `research/figures/`, referenced from the research note.

## Working style
- Start each session by reading `plan.md` and the latest note in `research/`.
- Work in small commits with descriptive messages.
- When a result looks too good, stop and write the "How this could be fooling us" section before doing anything else.
- Ask before adding a dependency, changing the universe, or altering cost assumptions.
- Do not place live orders. Broker integration is paper-only until the plan says otherwise.
