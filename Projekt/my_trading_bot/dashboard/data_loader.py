import os
import pickle
from collections import defaultdict
from functools import lru_cache

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT_DIR = os.path.join(BASE_DIR, "results")


def result_file_path(symbol: str, strategy: str) -> str:
    """Return the absolute path of the stored returns for a strategy/symbol."""
    return os.path.join(RESULT_DIR, f"{strategy}_{symbol}_returns.pkl")

def get_available_results():
    files = [f for f in os.listdir(RESULT_DIR) if f.endswith("_returns.pkl")]
    combos = []
    for f in files:
        name = f.replace("_returns.pkl", "")
        strat, symbol = name.split("_")
        combos.append((symbol, strat))
    return combos


def get_strategy_symbol_map():
    """Return a mapping from strategy name to the available symbols."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for symbol, strategy in get_available_results():
        mapping[strategy].append(symbol)
    return {strategy: sorted(set(symbols)) for strategy, symbols in mapping.items()}


def normalize_returns(data):
    """Convert various return/equity formats into a clean daily return series."""
    if data is None:
        return pd.Series(dtype=float)

    series = data
    if isinstance(series, pd.DataFrame):
        for candidate in [
            "returns",
            "ret",
            "r",
            "daily_return",
            "strategy_return",
        ]:
            if candidate in series.columns:
                series = series[candidate]
                break
        else:
            series = series.iloc[:, 0]

    series = pd.Series(series).copy()

    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index, errors="coerce")
    series = series[series.index.notna()].sort_index()

    if series.min() >= 0 and series.max() > 2:
        series = series.pct_change()

    series = series.groupby(series.index.normalize()).apply(
        lambda values: (1 + values).prod(axis=0) - 1
    )
    series = series.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    series = series.asfreq("B").fillna(0.0)

    try:
        series.index.freq = pd.tseries.offsets.BusinessDay()
    except Exception:
        pass

    series.name = "returns"
    return series


@lru_cache(maxsize=256)
def load_returns(symbol, strategy):
    file_path = result_file_path(symbol, strategy)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    return pd.Series()


@lru_cache(maxsize=256)
def load_normalized_returns(symbol: str, strategy: str) -> pd.Series:
    """Return cached, normalised daily returns for the given selection."""

    raw_returns = load_returns(symbol, strategy)
    if isinstance(raw_returns, pd.Series):
        # Ensure a fresh copy so callers do not mutate the cached series.
        raw_returns = raw_returns.copy()
    return normalize_returns(raw_returns)
