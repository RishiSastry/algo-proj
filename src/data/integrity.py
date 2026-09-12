"""Data-integrity checks over the cached price panel.

Checks per plan.md step 4:
- missing trading days (vs. the union trading calendar of the panel)
- zero or negative prices
- gaps > 5 trading days inside a ticker's history
- suspicious single-day moves (|return| > 50%), possible bad splits
"""

from __future__ import annotations

import pandas as pd

SUSPICIOUS_MOVE = 0.50
MAX_GAP_DAYS = 5


def missing_trading_days(closes: pd.DataFrame, universe: pd.DataFrame) -> dict[str, int]:
    """Count NaN closes per ticker between its ipo_date and panel end.

    The panel's own date index is used as the trading calendar, so this
    flags days where other tickers traded but this one has no bar.
    """
    out = {}
    for t in closes.columns:
        start = universe.loc[t, "ipo_date"] if t in universe.index else closes.index[0]
        sub = closes.loc[closes.index >= start, t]
        if sub.dropna().empty:
            out[t] = len(sub)
            continue
        sub = sub.loc[sub.first_valid_index():]
        n = int(sub.isna().sum())
        if n:
            out[t] = n
    return out


def bad_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Rows with zero or negative Open/High/Low/Close, as (date, ticker, field, value)."""
    rows = []
    for field in ["Open", "High", "Low", "Close"]:
        panel = prices[field]
        bad = panel[panel <= 0].stack().dropna()
        for (date, ticker), value in bad.items():
            rows.append((date, ticker, field, value))
    return pd.DataFrame(rows, columns=["date", "ticker", "field", "value"])


def long_gaps(closes: pd.DataFrame, max_gap: int = MAX_GAP_DAYS) -> pd.DataFrame:
    """Runs of > max_gap consecutive missing bars inside a ticker's history."""
    rows = []
    for t in closes.columns:
        s = closes[t]
        valid = s.dropna()
        if valid.empty:
            continue
        s = s.loc[valid.index[0] : valid.index[-1]]
        na = s.isna()
        if not na.any():
            continue
        group = (na != na.shift()).cumsum()
        for _, run in s[na].groupby(group[na]):
            if len(run) > max_gap:
                rows.append((t, run.index[0], run.index[-1], len(run)))
    return pd.DataFrame(rows, columns=["ticker", "gap_start", "gap_end", "n_days"])


def suspicious_moves(closes: pd.DataFrame, threshold: float = SUSPICIOUS_MOVE) -> pd.DataFrame:
    """Single-day |simple return| > threshold — candidate bad splits or data errors."""
    rets = closes.pct_change()
    hits = rets[rets.abs() > threshold].stack().dropna()
    rows = [(date, ticker, ret) for (date, ticker), ret in hits.items()]
    return pd.DataFrame(rows, columns=["date", "ticker", "return"])


def run_report(prices: pd.DataFrame, universe: pd.DataFrame) -> dict:
    closes = prices["Close"]
    return {
        "missing_days": missing_trading_days(closes, universe),
        "bad_prices": bad_prices(prices),
        "long_gaps": long_gaps(closes),
        "suspicious_moves": suspicious_moves(closes),
    }


def report_markdown(report: dict, closes: pd.DataFrame, universe: pd.DataFrame) -> str:
    lines = [
        "# Data integrity report",
        "",
        f"Panel: {closes.index[0].date()} → {closes.index[-1].date()}, "
        f"{closes.shape[1]} tickers, {closes.shape[0]} trading days.",
        "Prices: yfinance adjusted (auto_adjust=True — splits and dividends folded in).",
        "",
        "## Missing trading days (after ipo_date, within own history)",
    ]
    if report["missing_days"]:
        for t, n in sorted(report["missing_days"].items(), key=lambda kv: -kv[1]):
            lines.append(f"- {t}: {n} missing bars")
    else:
        lines.append("None.")

    lines += ["", "## Zero / negative prices"]
    bp = report["bad_prices"]
    lines.append("None." if bp.empty else bp.to_markdown(index=False))

    lines += ["", f"## Gaps > {MAX_GAP_DAYS} trading days"]
    lg = report["long_gaps"]
    lines.append("None." if lg.empty else lg.to_markdown(index=False))

    lines += ["", f"## Suspicious single-day moves (|return| > {SUSPICIOUS_MOVE:.0%})"]
    sm = report["suspicious_moves"]
    if sm.empty:
        lines.append("None.")
    else:
        sm = sm.copy()
        sm["return"] = sm["return"].map(lambda r: f"{r:+.1%}")
        lines.append(sm.to_markdown(index=False))
    return "\n".join(lines) + "\n"
