from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Available strategies exposed to the UI (keep UI unchanged; we expand here)
STRATEGY_LIST = ["Buy&Hold", "SMA(50/200)", "EMA(12/26)", "RSI(14)"]

# Make sure repo root is importable (keeps other relative imports working)
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Config ------------------------------------------------------------------
TS_URL: str | None = os.environ.get("TIMESCALE_URL")
DEFAULT_TABLE = os.environ.get("TS_TABLE", "ohlcv")

# Lazily create the SQLAlchemy engine so import-time doesn't explode
_engine: Engine | None = None
def get_engine() -> Engine:
    global _engine
    if _engine is None:
        if not TS_URL:
            raise RuntimeError(
                "TIMESCALE_URL not set. Export TIMESCALE_URL to use database-backed data."
            )
        _engine = create_engine(TS_URL, pool_pre_ping=True)
    return _engine

# --- Public helpers used by layouts/callbacks --------------------------------

def get_available_results() -> List[Tuple[str, str]]:
    """
    Return list of (symbol, strategy) pairs for the UI dropdowns.

    We derive symbols from the TimescaleDB OHLCV table and pair each symbol
    with all supported strategies in STRATEGY_LIST so the UI shows more choices.
    """
    try:
        eng = get_engine()
    except Exception:
        # If DB not configured yet, keep UI working with empty choices
        return []

    sql = text(f"SELECT DISTINCT symbol FROM {DEFAULT_TABLE} ORDER BY symbol;")
    with eng.connect() as conn:
        rows = conn.execute(sql).fetchall()
    symbols = [r[0] for r in rows]

    # Pair each symbol with all strategies
    return [(sym, strat) for sym in symbols for strat in STRATEGY_LIST]


def load_returns(symbol: str, strategy: str) -> pd.Series:
    """
    Load/compute returns series for the given symbol & strategy from TimescaleDB.

    Strategies:
      - "Buy&Hold": close-to-close daily returns
      - "SMA(50/200)": long when SMA(50) > SMA(200), flat otherwise
      - "EMA(12/26)": long when EMA(12) > EMA(26), flat otherwise
      - "RSI(14)": long when RSI<30 (simple oversold entry), flat otherwise

    Notes:
      * All returns are computed on daily last-close (business days).
      * Positions are applied with a one-day lag (next day open not available; this is a simple approximation).
    """
    if not symbol:
        return pd.Series(dtype="float64")

    eng = get_engine()

    sql = text(
        f"""
        SELECT datetime, close
        FROM {DEFAULT_TABLE}
        WHERE symbol = :symbol
        ORDER BY datetime
        """
    )
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn, params={"symbol": symbol})

    if df.empty:
        return pd.Series(dtype="float64")

    # Ensure datetime index and resample to business days
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df = df.set_index("datetime").sort_index()

    # Use last close per business day
    px = df["close"].resample("B").last().dropna()
    rets = px.pct_change().dropna()

    # --- Strategy routing ---
    strat = (strategy or "Buy&Hold").strip()

    if strat == "Buy&Hold":
        out = rets.copy()
    elif strat.startswith("SMA"):
        fast, slow = 50, 200
        sma_fast = px.rolling(fast, min_periods=fast).mean()
        sma_slow = px.rolling(slow, min_periods=slow).mean()
        pos = (sma_fast > sma_slow).astype(int).shift(1).reindex(rets.index).fillna(0)
        out = (rets * pos).dropna()
    elif strat.startswith("EMA"):
        fast, slow = 12, 26
        ema_fast = px.ewm(span=fast, adjust=False).mean()
        ema_slow = px.ewm(span=slow, adjust=False).mean()
        pos = (ema_fast > ema_slow).astype(int).shift(1).reindex(rets.index).fillna(0)
        out = (rets * pos).dropna()
    elif strat.startswith("RSI"):
        window = 14
        delta = px.diff()
        gain = delta.clip(lower=0).rolling(window, min_periods=window).mean()
        loss = (-delta.clip(upper=0)).rolling(window, min_periods=window).mean()
        rs = gain / loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))
        pos = (rsi < 30).astype(int).shift(1).reindex(rets.index).fillna(0)
        out = (rets * pos).dropna()
    else:
        # Fallback to Buy&Hold if unknown strategy is requested
        out = rets.copy()

    out.name = f"{symbol}-{strat}"
    return out