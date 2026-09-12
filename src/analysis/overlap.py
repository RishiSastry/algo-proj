"""Portfolio overlap: how much of the universe do we already own?

Reads a holdings file (portfolio/holdings.csv — gitignored, see
holdings.example.csv) and computes effective dollar exposure to each
universe ticker, both direct and looked-through ETFs.

Limitation, stated up front: yfinance exposes only an ETF's *top ~10*
holdings, so look-through exposure is a lower bound. Broad-index funds
(e.g. VTI/VOO) hold every universe large-cap below the top-10 cutoff;
treat the residual as "unknown, nonzero".
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

HOLDINGS_CSV = Path(__file__).resolve().parents[2] / "portfolio" / "holdings.csv"


def load_holdings(path: Path | None = None) -> pd.DataFrame:
    """holdings.csv: columns symbol, kind (stock|etf), market_value."""
    df = pd.read_csv(path or HOLDINGS_CSV)
    df["symbol"] = df["symbol"].str.upper()
    df["kind"] = df["kind"].str.lower()
    return df


def fetch_etf_top_holdings(etf: str) -> dict[str, float]:
    """Top-holdings weights for an ETF from yfinance (symbol -> weight).

    Returns {} when yfinance has no fund data for the symbol.
    """
    import yfinance as yf

    try:
        top = yf.Ticker(etf).funds_data.top_holdings
    except Exception:
        return {}
    if top is None or len(top) == 0:
        return {}
    return {str(sym).upper(): float(w) for sym, w in top["Holding Percent"].items()}


def effective_exposure(holdings: pd.DataFrame, universe_tickers: list[str],
                       etf_weights: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Per universe ticker: direct $, via-ETF $ (top-10 lower bound),
    total $, and share of total portfolio value."""
    total_value = holdings["market_value"].sum()
    rows = {t: {"direct": 0.0, "via_etf": 0.0} for t in universe_tickers}

    for _, h in holdings.iterrows():
        if h["kind"] == "stock" and h["symbol"] in rows:
            rows[h["symbol"]]["direct"] += h["market_value"]
        elif h["kind"] == "etf":
            for sym, w in etf_weights.get(h["symbol"], {}).items():
                if sym in rows:
                    rows[sym]["via_etf"] += h["market_value"] * w

    out = pd.DataFrame(rows).T
    out["total"] = out["direct"] + out["via_etf"]
    out["pct_of_portfolio"] = out["total"] / total_value
    return out.sort_values("total", ascending=False)


def overlap_report(holdings: pd.DataFrame, universe_tickers: list[str],
                   etf_weights: dict[str, dict[str, float]]) -> str:
    exp = effective_exposure(holdings, universe_tickers, etf_weights)
    held = exp[exp["total"] > 0]
    total_value = holdings["market_value"].sum()
    universe_share = held["total"].sum() / total_value
    lines = [
        "# Portfolio overlap with AI-infra universe",
        "",
        f"Portfolio value: ${total_value:,.0f}. Effective universe exposure: "
        f"${held['total'].sum():,.0f} (**{universe_share:.1%}**, top-10 ETF "
        "look-through only — true figure is higher).",
        "",
        held.assign(
            direct=held["direct"].map("${:,.0f}".format),
            via_etf=held["via_etf"].map("${:,.0f}".format),
            total=held["total"].map("${:,.0f}".format),
            pct_of_portfolio=held["pct_of_portfolio"].map("{:.2%}".format),
        ).to_markdown(),
    ]
    return "\n".join(lines) + "\n"
