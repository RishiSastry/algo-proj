"""Parquet price cache, one file per ticker under data/cache/.

Only missing date ranges are downloaded; anything cached is never
re-fetched (CLAUDE.md stack rules).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"

FIELDS = ["Open", "High", "Low", "Close", "Volume"]


def _path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker.upper()}.parquet"


def load(ticker: str) -> pd.DataFrame | None:
    """Return the cached OHLCV frame for a ticker, or None if absent."""
    p = _path(ticker)
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df.index = pd.to_datetime(df.index)
    return df


def save(ticker: str, df: pd.DataFrame) -> None:
    """Write a ticker's OHLCV frame to the cache (overwrites)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.sort_index().to_parquet(_path(ticker))


def load_meta(ticker: str) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """Covered (start, end) range for a ticker — the range already
    requested from the source, which may extend beyond the data itself
    (e.g. a request from before the ticker's first bar)."""
    p = _path(ticker).with_suffix(".meta.json")
    if not p.exists():
        return None
    raw = json.loads(p.read_text())
    return pd.Timestamp(raw["start"]), pd.Timestamp(raw["end"])


def save_meta(ticker: str, start: pd.Timestamp, end: pd.Timestamp) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(ticker).with_suffix(".meta.json")
    p.write_text(json.dumps({"start": str(start.date()), "end": str(end.date())}))


def merge(cached: pd.DataFrame | None, fresh: pd.DataFrame) -> pd.DataFrame:
    """Combine cached and freshly downloaded bars; fresh wins on overlap."""
    if cached is None or cached.empty:
        return fresh.sort_index()
    out = pd.concat([cached, fresh])
    out = out[~out.index.duplicated(keep="last")]
    return out.sort_index()


def last_expected_trading_day(end: pd.Timestamp) -> pd.Timestamp:
    """Most recent weekday on or before `end`.

    Ignores market holidays, so at worst one empty re-fetch happens on a
    holiday — never a re-download of data already cached.
    """
    d = end.normalize()
    while d.weekday() >= 5:
        d -= pd.Timedelta(days=1)
    return d
