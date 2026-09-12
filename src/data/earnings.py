"""Earnings dates and EPS surprises via yfinance, cached to Parquet.

Coverage note (checked 2026-09-12): yfinance returns up to ~100
quarters; mature names reach back to ~2002–2007, recent listings only a
few quarters. Announcement timestamps are kept so before/after-close
can be handled conservatively downstream.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

EARNINGS_CACHE = Path(__file__).resolve().parents[2] / "data" / "cache" / "earnings"


def fetch_earnings(ticker: str, refresh: bool = False) -> pd.DataFrame:
    """Reported earnings for one ticker: ann_date (tz-naive timestamp),
    eps_estimate, reported_eps, surprise_pct. Cached; refresh=True
    re-downloads."""
    p = EARNINGS_CACHE / f"{ticker.upper()}.parquet"
    if p.exists() and not refresh:
        return pd.read_parquet(p)

    import yfinance as yf

    raw = yf.Ticker(ticker).get_earnings_dates(limit=100)
    if raw is None or raw.empty:
        df = pd.DataFrame(columns=["ann_date", "eps_estimate", "reported_eps", "surprise_pct"])
    else:
        df = raw.rename(columns={
            "EPS Estimate": "eps_estimate",
            "Reported EPS": "reported_eps",
            "Surprise(%)": "surprise_pct",
        }).reset_index(names="ann_date")
        df["ann_date"] = pd.to_datetime(df["ann_date"]).dt.tz_localize(None)
        df = df.dropna(subset=["reported_eps"])  # drop future/scheduled rows
        df = df.drop_duplicates(subset="ann_date").sort_values("ann_date")
        df = df[["ann_date", "eps_estimate", "reported_eps", "surprise_pct"]]

    EARNINGS_CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    return df


def all_events(tickers: list[str]) -> pd.DataFrame:
    """Stacked events for many tickers: ticker, ann_date, surprise_pct."""
    frames = []
    for t in tickers:
        df = fetch_earnings(t)
        if df.empty:
            continue
        frames.append(df.assign(ticker=t))
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values("ann_date").reset_index(drop=True)
