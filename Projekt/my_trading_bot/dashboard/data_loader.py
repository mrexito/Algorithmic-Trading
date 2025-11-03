from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple
from glob import glob

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Available strategies exposed to the UI (keep UI unchanged; we expand here)
STRATEGY_LIST = ["Buy&Hold", "SMA(50/200)", "EMA(12/26)", "RSI(14)"]

# Make sure repo root is importable (keeps other relative imports working)
ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT.parent
for path in (str(ROOT), str(PROJECT_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

# --- Config ------------------------------------------------------------------
TS_URL: str | None = os.environ.get("TIMESCALE_URL")
DEFAULT_TABLE = os.environ.get("TS_TABLE", "ohlcv")
# Static fallback directory with historical CSVs (per-symbol) used if DB is unavailable
HIST_DIR = (ROOT / "Projekt" / "my_trading_bot" / "data" / "historical_prices").resolve()

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

# --- Startup bootstrap -------------------------------------------------------
BOOTSTRAP_SYMBOLS = tuple(
    sym.strip().upper()
    for sym in os.environ.get("MARKET_BOOTSTRAP_SYMBOLS", "AAPL,GOOGL").split(",")
    if sym.strip()
)
BOOTSTRAP_DURATION = os.environ.get("MARKET_BOOTSTRAP_DURATION", "5 D")
BOOTSTRAP_BAR_SIZE = os.environ.get("MARKET_BOOTSTRAP_BAR_SIZE", "5 min")
_bootstrap_completed = False


def bootstrap_live_data(
    symbols: Iterable[str] | None = None,
    duration: str | None = None,
    bar_size: str | None = None,
    provider: str = "yf",
) -> None:
    """Fetch live data for default symbols and upsert into the configured backend."""
    global _bootstrap_completed
    if _bootstrap_completed:
        return

    # Resolve inputs and sanitize symbol list
    raw_symbols = list(symbols) if symbols is not None else list(BOOTSTRAP_SYMBOLS)
    parsed_symbols = [sym.strip().upper() for sym in raw_symbols if sym and sym.strip()]
    if not parsed_symbols:
        return
    duration = duration or BOOTSTRAP_DURATION
    bar_size = bar_size or BOOTSTRAP_BAR_SIZE
    if provider != "yf":
        print(f"[Bootstrap] Unsupported provider '{provider}'. Skipping bootstrap.")
        _bootstrap_completed = True
        return

    try:
        from Projekt.my_trading_bot.data import market_data_api
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[Bootstrap] Unable to import market data API: {exc}")
        return

    engine: Engine | None = None
    if TS_URL:
        try:
            engine = get_engine()
        except Exception as exc:
            print(f"[Bootstrap] Database unavailable ({exc}). Proceeding without TimescaleDB.")
            engine = None
    else:
        print("[Bootstrap] TIMESCALE_URL not set. Data will only be cached as CSV snapshots.")

    print(f"[Bootstrap] Loading symbols {', '.join(parsed_symbols)} (duration={duration}, bar={bar_size})")
    for symbol in parsed_symbols:
        try:
            df = market_data_api.fetch_yahoo(symbol, duration, bar_size)
        except Exception as exc:  # pragma: no cover - network dependency
            print(f"[Bootstrap] ERROR fetching {symbol}: {exc}")
            continue

        if df.empty:
            print(f"[Bootstrap] No data returned for {symbol}.")
            continue

        try:
            path = market_data_api.save_csv(df, symbol)
            print(f"[Bootstrap] Cached {symbol} snapshot at {path} (rows={len(df)}).")
        except Exception as exc:
            print(f"[Bootstrap] WARNING: Failed to cache CSV for {symbol}: {exc}")

        if engine is None:
            continue
        try:
            rows = market_data_api.upsert_timescale(df, engine, DEFAULT_TABLE)
            print(f"[Bootstrap] Upserted {rows} rows for {symbol} into table '{DEFAULT_TABLE}'.")
        except Exception as exc:  # pragma: no cover - DB specific
            print(f"[Bootstrap] ERROR upserting {symbol}: {exc}")

    _bootstrap_completed = True

# --- Fallback helpers ---------------------------------------------------------

def _list_symbols_on_disk() -> list[str]:
    """Return list of symbols inferred from CSV filenames in HIST_DIR (e.g., AAPL.csv)."""
    if not HIST_DIR.exists():
        return []
    files = glob(str(HIST_DIR / "*.csv"))
    symbols = []
    for fp in files:
        name = Path(fp).stem
        if name:
            symbols.append(name.upper())
    return sorted(set(symbols))


def _load_px_from_csv(symbol: str) -> pd.Series:
    """Load a close-price daily series from historical CSV fallback.

    Expects columns at least: datetime, close
    """
    fp = HIST_DIR / f"{symbol.upper()}.csv"
    if not fp.exists():
        return pd.Series(dtype="float64")
    df = pd.read_csv(fp)
    if df.empty or "datetime" not in df.columns or "close" not in df.columns:
        return pd.Series(dtype="float64")
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
    df = df.dropna(subset=["datetime", "close"]).sort_values("datetime")
    s = df.set_index("datetime")["close"].asfreq("B", method="pad").dropna()
    s.name = symbol.upper()
    return s

# --- Public helpers used by layouts/callbacks --------------------------------

def get_available_results() -> List[Tuple[str, str]]:
    """
    Return list of (symbol, strategy) pairs for the UI dropdowns.

    Primary source: TimescaleDB (distinct symbols in OHLCV table).
    Fallback: infer symbols from CSVs in data/historical_prices when DB is missing/unreachable.
    """
    symbols: list[str] = []
    # Try DB first
    try:
        eng = get_engine()
        sql = text(f"SELECT DISTINCT symbol FROM {DEFAULT_TABLE} ORDER BY symbol;")
        with eng.connect() as conn:
            rows = conn.execute(sql).fetchall()
        symbols = [str(r[0]).upper() for r in rows]
    except Exception:
        symbols = _list_symbols_on_disk()

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

    # Try DB first
    df = pd.DataFrame()
    try:
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
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        # Fallback to static CSV on disk
        px = _load_px_from_csv(symbol)
    else:
        # Normalize DB payload -> daily last close
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        df = df.set_index("datetime").sort_index()
        px = df["close"].resample("B").last().dropna()

    if px is None or px.empty:
        return pd.Series(dtype="float64")

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
        out = rets.copy()

    out.name = f"{symbol}-{strat}"
    return out


# --- Backend status helper ---------------------------------------------------
def get_backend_status() -> str:
    """
    Return a short status string indicating which backend is currently reachable.
    Priority: TimescaleDB (if TIMESCALE_URL is set and connection succeeds); else CSV; else 'None'.
    """
    # Try DB
    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "TimescaleDB"
    except Exception:
        pass

    # CSV fallback?
    symbols = _list_symbols_on_disk()
    if symbols:
        return "CSV fallback"
    return "None"
