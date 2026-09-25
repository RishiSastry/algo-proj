"""Price fetching via yfinance, backed by the Parquet cache.

All prices are adjusted (yfinance auto_adjust=True: splits and dividends
folded into OHLC). Index is tz-naive, trading days only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

from src.data import cache

UNIVERSE_CSV = Path(__file__).resolve().parents[2] / "universe" / "universe.csv"

DEFAULT_START = "2005-01-01"


def load_universe() -> pd.DataFrame:
    """Universe file with parsed ipo_date, indexed by ticker."""
    df = pd.read_csv(UNIVERSE_CSV, parse_dates=["ipo_date"])
    return df.set_index("ticker")


def universe_tickers(include_benchmarks: bool = False) -> list[str]:
    u = load_universe()
    if not include_benchmarks:
        u = u[u["bucket"] != "benchmark"]
    return list(u.index)


def _download(ticker: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    hist = yf.Ticker(ticker).history(
        start=start, end=end + pd.Timedelta(days=1), auto_adjust=True
    )
    if hist.empty:
        return pd.DataFrame(columns=cache.FIELDS)
    hist.index = pd.to_datetime(hist.index).tz_localize(None).normalize()
    # vendor outages can return rows with volume but NaN prices; caching
    # those would poison the store permanently (2026-09-21 incident).
    # A bar without a close is not a bar.
    out = hist[cache.FIELDS]
    return out[out["Close"].notna()]


def get_ticker(ticker: str, start=DEFAULT_START, end=None) -> pd.DataFrame:
    """OHLCV for one ticker over [start, end], hitting the network only
    for date ranges the cache does not already hold."""
    start = pd.Timestamp(start)
    end = cache.last_expected_trading_day(
        pd.Timestamp(end) if end is not None else pd.Timestamp.today()
    )
    cached = cache.load(ticker)
    covered = cache.load_meta(ticker)

    if cached is None or covered is None:
        df = _download(ticker, start, end)
        cache.save(ticker, df)
        cache.save_meta(ticker, start, end)
    else:
        df = cached
        cov_start, cov_end = covered
        fetched = False
        if start < cov_start:
            head = _download(ticker, start, cov_start - pd.Timedelta(days=1))
            df = cache.merge(head if not head.empty else None, df)
            fetched = True
        new_cov_end = cov_end
        if end > cov_end:
            tail = _download(ticker, cov_end + pd.Timedelta(days=1), end)
            if not tail.empty:
                df = cache.merge(df, tail)
                new_cov_end = end
            # empty tail (holiday or vendor outage): do NOT extend
            # coverage — retry the range on the next call
            fetched = True
        if fetched:
            cache.save(ticker, df)
            cache.save_meta(ticker, min(start, cov_start), new_cov_end)

    return df.loc[(df.index >= start) & (df.index <= end)]


def fetch_prices(tickers: list[str], start=DEFAULT_START, end=None) -> pd.DataFrame:
    """Adjusted OHLCV for many tickers.

    Returns a DataFrame with MultiIndex columns (field, ticker) — e.g.
    prices["Close"] is a dates × tickers close-price panel.
    """
    frames = {}
    for t in tickers:
        df = get_ticker(t, start=start, end=end)
        if df.empty:
            continue
        frames[t] = df
    panel = pd.concat(frames, axis=1)  # (ticker, field)
    panel = panel.swaplevel(axis=1).sort_index(axis=1)  # (field, ticker)
    panel.columns.names = ["field", "ticker"]
    return panel


def closes(tickers: list[str] | None = None, start=DEFAULT_START, end=None) -> pd.DataFrame:
    """Adjusted close panel (dates × tickers) for the given tickers,
    defaulting to the full universe plus benchmarks."""
    if tickers is None:
        tickers = universe_tickers(include_benchmarks=True)
    return fetch_prices(tickers, start=start, end=end)["Close"]
