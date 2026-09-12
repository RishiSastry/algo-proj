import numpy as np
import pandas as pd

from src.analysis.pairs import candidate_pairs, hedge_ratio, scan


def synthetic_universe():
    return pd.DataFrame(
        {"bucket": ["chip", "chip", "chip", "benchmark"],
         "ipo_date": [pd.Timestamp("2010-01-01")] * 4},
        index=["COINT_A", "COINT_B", "RANDOM_C", "SPY"])


def synthetic_closes(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=n)
    common = np.cumsum(rng.normal(0, 0.01, n))
    spread = np.zeros(n)
    for i in range(1, n):  # strongly mean-reverting spread
        spread[i] = 0.9 * spread[i - 1] + rng.normal(0, 0.01)
    a = 100 * np.exp(common + spread)
    b = 50 * np.exp(common)
    c = 80 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))  # independent walk
    return pd.DataFrame({"COINT_A": a, "COINT_B": b, "RANDOM_C": c,
                         "SPY": 100.0}, index=idx)


def test_candidate_pairs_within_bucket_excludes_benchmarks():
    pairs = candidate_pairs(synthetic_closes(), synthetic_universe(), split="2018-01-01")
    assert ("COINT_A", "COINT_B") in pairs
    assert all("SPY" not in p for p in pairs)


def test_hedge_ratio_recovers_relationship():
    closes = synthetic_closes()
    la, lb = np.log(closes["COINT_A"]), np.log(closes["COINT_B"])
    _, beta = hedge_ratio(la, lb)
    assert 0.8 < beta < 1.2  # true relationship is 1:1 in logs


def test_scan_finds_planted_pair_and_rejects_random():
    result = scan(synthetic_closes(), synthetic_universe(), split="2018-01-01")
    row = result[result["pair"] == "COINT_A/COINT_B"].iloc[0]
    assert row["train_pass"]
    assert row["oos_adf_p"] < 0.05
    random_rows = result[result["pair"].str.contains("RANDOM_C")]
    assert not random_rows["train_pass"].any()
