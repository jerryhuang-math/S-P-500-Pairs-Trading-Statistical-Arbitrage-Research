"""Historical three-month Treasury benchmark shared by notebooks 03 and 04.

DGS3MO is an annual percentage yield on an investment basis, not a total-return
index. The benchmark approximates rolling bills using effective daily accrual
on the same 252-session convention as the strategy. It excludes price changes.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO"
DEFAULT_CACHE = Path(__file__).resolve().parents[1] / "data" / "risk_free" / "DGS3MO.csv"


@lru_cache(maxsize=None)
def load_treasury_yields(cache_path=DEFAULT_CACHE):
    """Read a reproducible local snapshot; download from FRED if absent.

    Delete the snapshot and restart the kernel to refresh it. Missing coverage
    raises during alignment rather than silently substituting zero interest.
    """
    path = Path(cache_path)
    frame = pd.read_csv(path if path.exists() else FRED_URL, na_values=["."])
    dates = pd.to_datetime(frame.iloc[:, 0], errors="raise")
    yields = pd.Series(pd.to_numeric(frame["DGS3MO"], errors="raise").to_numpy(),
                       index=dates, name="DGS3MO").dropna().sort_index()
    if yields.empty or not yields.index.is_unique or not np.isfinite(yields).all():
        raise ValueError("Invalid DGS3MO Treasury observations")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    return yields


def annualized_treasury_return(dates, yields=None, trading_days=252):
    """Compound lagged historical yields and annualize over these sessions.

    Use only observations strictly before each session (no lookahead). Carry
    rates across weekends/holidays for at most seven calendar days. A constant
    5% quoted yield produces a 5% annualized benchmark for any period length.
    """
    dates = pd.DatetimeIndex(dates)
    if dates.empty or not dates.is_unique or not dates.is_monotonic_increasing:
        raise ValueError("Benchmark dates must be nonempty, unique, and sorted")
    yields = load_treasury_yields() if yields is None else yields.dropna().sort_index()
    if not yields.index.is_unique:
        raise ValueError("Duplicate Treasury observation dates")
    aligned = yields.reindex(dates - pd.Timedelta(days=1), method="ffill",
                             tolerance=pd.Timedelta(days=7)).to_numpy(dtype=float) / 100
    if not np.isfinite(aligned).all() or (aligned <= -1).any():
        raise ValueError("Missing or invalid historical DGS3MO coverage for backtest dates; refresh the Treasury CSV")
    daily_log_returns = np.log1p(aligned) / trading_days
    return float(np.expm1(daily_log_returns.sum() * trading_days / len(dates)))
