# plan.md — Roadmap and Session One Spec

## Goals
- **Learning goal:** understand markets, options, quant research methodology, and the tech behind a systematic model.
- **Deliverable:** a backtested, walk-forward-validated strategy on the AI-infrastructure universe, running paper trades through a broker API.
- **Return target:** beat buy-and-hold SPY *and* an equal-weight basket of the universe on a risk-adjusted basis. Aspirational: ~15–20% annualized with survivable drawdowns.
- **Capital plan:** Phase 1 = $1K cash, stocks/ETFs only, process-driven (20–30 journaled trades, system followed on every one). Phase 2 = small sliver of existing portfolio, options overlay unlocked, gated on walk-forward validation + paper trading.
- **Explicitly out of scope:** day trading, HFT, margin/leverage, discretionary thesis trades.

## Universe (candidate — VERIFY in session one)
Each ticker must be checked for: still listed, average daily dollar volume > $50M, IPO date recorded. Drop or flag anything that fails.

| Bucket | Tickers (candidates) |
|---|---|
| Hyperscalers | MSFT, AMZN, GOOGL, META, ORCL |
| Chipmakers & fab | NVDA, AMD, AVGO, TSM, MRVL, MU, ARM, ASML, QCOM, INTC |
| Neoclouds / AI data centers | CRWV, NBIS, IREN, APLD, WULF, CORZ, CIFR, HUT |
| Supporting hardware / networking / power | SMCI, DELL, ANET, VRT |
| Benchmarks | SPY, SMH (sector), equal-weight universe (computed) |

Notes:
- "Neo labs" (OpenAI, Anthropic, etc.) are private. Exposure only via hyperscalers. Revisit if any IPO.
- Neoclouds are recent IPOs / pivots with short histories — expect 1–3 years of data. Survivorship-bias handling (CLAUDE.md #4) is critical here.
- Many of these names are likely already held via broad ETFs in the existing portfolio. Session two quantifies that overlap.

## Session One — Build Spec (paste into Claude Code)
> Read CLAUDE.md and plan.md first. Then build the following, committing after each numbered step.

1. **Scaffold.** `uv init`, `pyproject.toml` with pandas, numpy, matplotlib, scipy, statsmodels, yfinance, pyarrow, pytest. Create the layout in CLAUDE.md. `.gitignore` covering `data/cache/`, notebooks checkpoints, `.venv`. `git init` + first commit.
2. **Universe file.** `universe/universe.csv` with columns `ticker,name,bucket,ipo_date,notes` from the candidate table above. For each ticker, fetch first available date from yfinance and record it as `ipo_date` (approximate is fine; note where yfinance history starts later than the true IPO).
3. **Data layer.** `src/data/fetch.py`: `fetch_prices(tickers, start="2005-01-01", end=None) -> DataFrame` (MultiIndex columns: field × ticker, adjusted). `src/data/cache.py`: Parquet cache keyed by ticker; only fetch missing date ranges. Pull the full universe + SPY + SMH.
4. **Integrity checks.** `src/data/integrity.py`: report missing trading days, zero/negative prices, gaps > 5 days, suspicious splits (single-day |return| > 50%). Write results to `research/YYYY-MM-DD-data-integrity.md`. Add `tests/test_integrity.py`.
5. **Returns & stats.** `src/analysis/returns.py` (simple, log, rolling vol, drawdown series). `src/analysis/stats.py`: `summary_stats(returns) -> dict` with CAGR, ann. vol, Sharpe (rf=0 for now), Sortino, max DD, Calmar. Print the table for SPY, SMH, and each ticker.
6. **Equal-weight benchmark.** `src/analysis/benchmarks.py`: equal-weight, monthly-rebalanced basket of the universe, only including tickers after `ipo_date + 60 trading days`. This is benchmark (b) for everything that follows.
7. **Factor check.** `src/analysis/factor.py`: rolling 60-day pairwise correlation matrix of the universe, and the fraction of variance explained by the first principal component. Plot both. This measures "how much is this really one bet." Write findings to `research/YYYY-MM-DD-factor-structure.md`.
8. **Backtest engine v0.** `src/backtest/engine.py`: takes a weights DataFrame (dates × tickers), shifts signals by one day, applies costs from `src/backtest/costs.py` (5 bps slippage + spread estimate), computes portfolio returns, turnover, exposure. `src/backtest/metrics.py` wraps `summary_stats` and adds comparison vs. both benchmarks. Add `tests/test_no_lookahead.py` that fails if a weight at date t depends on prices at date t.
9. **First strategy.** `src/strategies/momentum_xs.py`: cross-sectional momentum — at each month-end, rank universe by trailing 6-month return (skip most recent month), hold top third equal-weight, rebalance monthly. Run it through the engine. Save equity curve + drawdown plot to `research/figures/`.
10. **Research note.** `research/YYYY-MM-DD-momentum-xs-v0.md`: setup, results vs. both benchmarks, in-sample only (label it clearly), and a full "How this could be fooling us" section. Do NOT tune parameters yet.
11. **Update plan.md** with what was built, what broke, and open questions.

Deliverable check for session one: `uv run pytest` passes, `research/` has three notes, and I can read the momentum result against both benchmarks.

## Session One — Completed 2026-09-12

**Built:** all 11 steps. 17 tests pass (`uv run pytest`). Three research
notes in `research/`: data integrity, factor structure, momentum-xs v0.

**Universe findings:** all 29 candidates listed and pass the $50M
liquidity screen (thinnest: CORZ ~$263M/day). Several yfinance histories
belong to predecessor entities — WULF (IKONICS), CIFR (SPAC shell), HUT
(pre-merger TSX era), DELL (Class V tracking), VRT (SPAC), NBIS
(pre-halt Yandex), CORZ (pre-Ch.11 listing) — `ipo_date` was overridden
to the current entity's effective listing date and all earlier data is
masked in analysis and backtests.

**Key results (in-sample, net of costs, 2005-09 → 2026-09):**
- Equal-weight universe benchmark (b): 29.7% CAGR, Sharpe 1.01 — a very
  high bar, largely NVDA + survivor/hindsight bias in universe choice.
- Factor structure: avg pairwise corr 0.39, PC1 ≈ 45% of variance,
  spiking >0.7 in stress years — the universe is roughly one bet in
  drawdowns. Cross-sectional/long-short designs are the honest path.
- Momentum-xs v0 (6-1, top third, monthly): 30.1% CAGR, Sharpe 0.90 —
  beats SPY, but **loses to benchmark (b) on Sharpe/Sortino/Calmar. v0
  added nothing (CLAUDE.md #5). Do not tune; test new hypotheses.**

**What broke along the way:** pandas 3.0's `stack()` no longer drops
NaNs (fixed with `.dropna()`); naive cache re-fetched empty head/tail
ranges every call (fixed with covered-range sidecar metadata).

**Open questions added:**
- Benchmark (b) is itself survivorship-flattered; consider adding SMH
  as a third reference in reports since it is investable and unbiased.
- Cost model's half-spread ladder is a static 2026-liquidity guess;
  needs era-aware or quote-based estimates before conclusions get fine.
- Momentum variants (vol-scaling, other lookbacks) must go through the
  session-5 robustness-surface protocol, not one-off tuning.

## Roadmap after session one
- **Session 2:** portfolio overlap analysis (existing holdings vs. universe); trade journal template; walk-forward framework (rolling train/test windows). — DONE 2026-09-12 (overlap **tooling** done; actual analysis blocked on holdings file, see below)
- **Session 3:** second strategy family — post-earnings drift (needs earnings dates); compare to momentum on the same engine. — DONE 2026-09-12
- **Session 4:** pairs / long-short within the universe to reduce single-factor exposure. — DONE 2026-09-12 (long-short momentum; pairs deferred, see next steps)
- **Session 5:** parameter robustness — sensitivity surfaces, not point optimization. Kill anything fragile. — DONE 2026-09-12
- **Session 6:** broker paper-trading integration (Alpaca or Schwab API). Daily headless run via `claude -p` + cron that refreshes data, reruns backtests, and writes a summary. — PARTIAL: `scripts/daily_update.py` (headless refresh + integrity + daily log, cron-ready) is done; broker half **blocked on Rishi**: choose Alpaca vs Schwab, provide paper-API keys, approve the SDK dependency.
- **Phase 2 gate review:** walk-forward results, paper-trade log, then decide on portfolio sliver + options overlay (covered calls / cash-secured puts).

## Sessions 2–5 — Completed 2026-09-12

**Built:** overlap tool with ETF look-through (`src/analysis/overlap.py` +
`portfolio/holdings.example.csv`; real holdings gitignored); trade
journal (`journal/`); walk-forward framework (`src/backtest/walkforward.py`);
earnings data layer (`src/data/earnings.py`, ~1,600 cached events, mature
names back to ~2002); PEAD strategy; long-short support in the engine
(gross-exposure budget + reporting); robustness-surface tooling
(`src/analysis/robustness.py`); headless daily refresh
(`scripts/daily_update.py`). 27 tests pass. Five new research notes.

**Findings (all net of costs, vs. both benchmarks):**
1. **Momentum, walk-forward OOS (2008–2026, 37 folds): adds nothing.**
   OOS Sharpe 0.90 vs EW basket 1.03; parameter selection ties the
   untuned 6-1 default; chosen params scatter (no stable winner).
2. **Long-short momentum: zero alpha.** Dollar-neutral book earns ~0%
   CAGR over 21 years (Sharpe 0.07) while factor correlation drops to
   0.12 — long-only momentum's 30% CAGR was entirely sector beta.
3. **PEAD: beta in a costume.** Sharpe monotone in hold length
   (10d: 0.38 → 63d: ~1.0 = the basket), flat in surprise threshold —
   the earnings signal itself contributes nothing; the family kill is
   robust across a 16-cell surface.
4. **Momentum kills are robust:** 30-cell surfaces are flat plateaus
   (LO median 0.92, all ≤ 1.02; LS median 0.03). Nothing fragile was
   kept; nothing worth tuning exists in these families.
5. Snoop ledger on this sample now ≈ 88 backtests. Treat any future
   in-grid "discovery" as noise.

**Strategic read:** long-only tilts converge to benchmark (b); the
one neutralized book is zero. Next promising directions are managing
the factor itself (time-series/regime signals, vol targeting on the
basket), pairs/spreads on economically linked subsets, and combining
return *shapes* (PEAD's cash-heavy profile) at the portfolio level.

**Blocked on Rishi:**
- Overlap analysis: fill in `portfolio/holdings.csv` (columns:
  symbol,kind,market_value — see the example file), then run
  `src/analysis/overlap.py` report. Note: yfinance exposes only top-10
  ETF holdings, so look-through is a lower bound.
- Session 6 broker half: pick Alpaca vs Schwab, provide paper keys,
  approve the dependency.
- Optional: install the daily cron —
  `30 18 * * 1-5 cd ~/algo-proj && uv run python scripts/daily_update.py`.

## Sessions 7–8 — Completed 2026-09-12

**Session 7 — basket timing (`src/strategies/basket_timing.py`):**
- **Trend filter (10-month rule on the EW basket) is the program's
  first survivor: walk-forward OOS net Sharpe 1.17 vs EW basket 1.03
  and SPY 0.64 over the identical 2008–2026 window.** Max drawdown
  roughly halves (-32% vs -61%), turnover 1.4×/yr; the edge is
  drawdown control, not extra return (in-sample CAGR 25.5% vs basket
  29.1%). Surfaces are plateaus (all MA windows ≥ basket Sharpe);
  fold selection is stable (ma105 in 22/37 folds). Caveat honored in
  the note: the edge rests on ~4 regime exits — wide error bars.
- Vol targeting (20%/63d): Sharpe 1.03, milder improvement; candidate
  overlay for later, untested in combination (pre-register first).
- **Graduates to paper trading once the broker leg exists.**

**Session 8 — pairs scan (`src/analysis/pairs.py`):**
- 46 within-bucket pairs, Engle-Granger on pre-2018 train with
  Bonferroni correction, hedge-ratio-frozen OOS ADF on 2018–2026.
  **Zero survivors.** The 3 pairs a naive α=0.05 scan would have
  "found" all fail OOS — multiple-testing correction prevented three
  fake strategies. No pairs trading on this universe; revisit neocloud
  pairs ~2027+ when post-pivot histories reach 5 years.

## Session 9 — Completed 2026-09-12

- **Trend × vol-target combo: rejected.** Sharpe 0.98 / Calmar 0.61 vs
  trend-only's 1.05 / 0.81 — the two signals hedge the same episodes,
  so stacking double-counts the de-risking. Trend-only stays the core
  sleeve; no more overlay variants against this sample.
- **$1K whole-share implementation is infeasible:** $37/name budget vs
  ~$225 median share price; only the 4 junkiest names are affordable.
  **Fractional shares are a hard requirement → Alpaca** (Schwab
  fractional covers only S&P 500 slices). Alternative to price out:
  SMH as basket proxy for the trend signal.

## Session 10 — Completed 2026-09-13 (broker = Schwab)

**Decision (Rishi): Schwab.** Consequences handled:
- Schwab has no fractional shares outside S&P 500 Slices and **no
  paper-trading API sandbox** (paperMoney is thinkorswim-only). So:
- **Paper phase runs in an internal simulator** (`src/paper/simulator.py`,
  `scripts/paper_trade.py`) — real cached prices, t+1 open execution,
  10 bps/side costs, idempotent daily runs. No broker needed until
  real money.
- **Two paper books started 2026-09-13, $1K each, signal currently IN:**
  `paper/basket` (fractional, strategy-faithful trend sleeve) and
  `paper/smh` (whole-share SMH proxy — the only faithful $1K Schwab
  expression). SMH-proxy backtest: Sharpe 0.75 vs basket's 1.05 — the
  proxy is honest but expensive (see 2026-09-13-smh-proxy.md); the
  forward race between the books feeds the Phase-2 gate.
- **Cron installed** (weekdays 18:30): data refresh + integrity +
  paper trade, logging to `logs/cron.log` and `research/daily-log.md`.
  Caveats: the Mac must be awake at 18:30; macOS may require granting
  cron Full Disk Access (System Settings → Privacy) if logs stay empty.

**Phase 2 prerequisites (when real money starts, not before):**
- Schwab Trader API: developer.schwab.com account → create app → OAuth
  handshake; `schwab-py` is the likely client library (dependency —
  needs approval then).
- Phase-2 capital sizing note: whole-share EW basket needs ≈ $45K+ to
  track well; below that, the SMH proxy remains the Schwab expression.

**Overlap report delivered 2026-09-13, updated same day**
(research/2026-09-13-portfolio-overlap.md): including ≈$44K of locked
work AMZN at Morgan Stanley, total wealth in scope is ≈$92K and
**≥70% is AI-infra universe exposure** (AMZN 48% — employer stock —
NVDA 20%, CRWV 2%). Flag for the Phase-2 gate: adding a long sleeve
adds to that concentration; the signal's de-risking use may matter
more than its return use.

**Trading mandate (Rishi, 2026-09-13): all trading happens in the
Schwab individual account ONLY.** The Morgan Stanley account (work
AMZN) and any other accounts are untouchable. Phase-1 $1K comes from
Schwab cash (~$2.1K available). Open question for Rishi: the strategy
universe includes AMZN — given 48% locked exposure, should the
*tradable* sleeve exclude AMZN? That is a universe change and needs
explicit sign-off either way (CLAUDE.md working style).

## Curriculum thread (with Claude in chat)
Concepts taught on demand, against real data from this repo, in roughly this order:
market microstructure → returns & volatility → the sin list (overfitting, lookahead, survivorship, snooping) → cross-sectional vs. time-series strategies → factor/correlation structure → walk-forward validation → options fundamentals & the Greeks → volatility risk premium → execution & broker APIs.

## Open questions
- Data source upgrade path if yfinance proves unreliable (Polygon, Tiingo, Alpaca data).
- Which broker API for paper trading: Alpaca (easiest) vs. Schwab (where the money is).
- Handling of ARM/ASML/TSM as ADRs / foreign listings — FX and hours effects.
