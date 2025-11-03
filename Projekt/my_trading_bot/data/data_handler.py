"""Market data loader: Yahoo Finance fetch + TimescaleDB upsert (CLI entrypoint).

Usage:
  python -m Projekt.my_trading_bot.data.market_data_api AAPL --provider yf --duration "5 D" --bar-size "5 min"

Env vars:
  TIMESCALE_URL   SQLAlchemy URL for Timescale/Postgres, e.g. postgresql+psycopg2://postgres:postgres@localhost:5432/market
  TS_TABLE        Target table name (default: ohlcv)
"""

from __future__ import annotations

import os
import sys
import argparse
from datetime import timezone

import pandas as pd

# Lazy import so the module can be imported without optional deps when not used
try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# --- Helpers -----------------------------------------------------------------

INTERVAL_MAP = {
    "1 min": "1m",
    "2 min": "2m",
    "5 min": "5m",
    "15 min": "15m",
    "30 min": "30m",
    "60 min": "60m",
    "90 min": "90m",
    "1 hour": "60m",
    "1 day": "1d",
}

PERIOD_MAP = {
    # yfinance period strings
    "1 D": "1d",
    "2 D": "2d",
    "5 D": "5d",
    "1 W": "5d",  # yfinance doesn't have 1w for intraday; leave as 5d fallback
    "1 Mo": "1mo",
    "3 Mo": "3mo",
    "6 Mo": "6mo",
    "1 Y": "1y",
    "2 Y": "2y",
    "5 Y": "5y",
    "10 Y": "10y",
    "Max": "max",
}

LIVE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # -> Projekt/my_trading_bot
    "data",
    "live_data",
)

DEFAULT_TABLE = os.environ.get("TS_TABLE", "ohlcv")
TS_URL = os.environ.get("TIMESCALE_URL")


# --- Yahoo Finance fetch ------------------------------------------------------

def _normalize_ohlcv(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Normalize a yfinance dataframe to columns [datetime, open, high, low, close, volume, symbol]."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume", "symbol"])

    # yfinance returns columns like ['Open','High','Low','Close','Adj Close','Volume']
    # and DateTimeIndex (tz-aware). We keep OHLCV and convert index to a column.
    expected = {"Open", "High", "Low", "Close", "Volume"}
    missing = expected.difference(set(map(str, df.columns)))
    if missing:
        # Some variants may return a single-level with ticker prefix; handle MultiIndex too
        if isinstance(df.columns, pd.MultiIndex):
            # Try to select the first level (ticker) and standard OHLCV names
            first = (
                df.xs(symbol, axis=1, level=0, drop_level=False)
                if symbol in df.columns.get_level_values(0)
                else df.copy()
            )
            # Flatten
            first.columns = [c[-1] if isinstance(c, tuple) else c for c in first.columns]
            df = first
        # Re-check
        missing = expected.difference(set(map(str, df.columns)))
        if missing:
            raise RuntimeError(
                f"Unexpected yfinance columns: {list(map(str, df.columns))} — missing one of required OHLCV columns"
            )

    out = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    out.columns = ["open", "high", "low", "close", "volume"]

    # Ensure index is tz-aware UTC and move to column
    idx = pd.to_datetime(out.index)
    if idx.tz is None:
        idx = idx.tz_localize(timezone.utc)
    else:
        idx = idx.tz_convert(timezone.utc)
    out.insert(0, "datetime", idx)

    out["symbol"] = symbol
    # Sort & drop obvious duplicates
    out = (
        out.dropna(subset=["datetime"])
           .drop_duplicates(subset=["datetime", "symbol"])
           .sort_values("datetime")
           .reset_index(drop=True)
    )
    return out


def fetch_yahoo(symbol: str, duration: str, bar_size: str) -> pd.DataFrame:
    if yf is None:
        raise ImportError("yfinance is not installed. Please `pip install yfinance`. ")

    # Map inputs to yfinance period/interval
    period = PERIOD_MAP.get(duration, duration.lower().replace(" ", ""))
    interval = INTERVAL_MAP.get(bar_size, bar_size)

    # yfinance constraints: intraday intervals are limited to certain period ranges
    # We'll rely on yfinance to validate and raise if unsupported.
    data = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
    df = _normalize_ohlcv(data, symbol)
    return df


# --- TimescaleDB upsert -------------------------------------------------------

def _ensure_table(engine: Engine, table: str) -> None:
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table} (
        symbol TEXT NOT NULL,
        datetime TIMESTAMPTZ NOT NULL,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION,
        volume BIGINT,
        PRIMARY KEY (symbol, datetime)
    );
    """
    # Mark as hypertable if not already
    hypertable_sql = f"""
    SELECT create_hypertable('{table}', 'datetime', if_not_exists => TRUE);
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql))
        try:
            conn.execute(text(hypertable_sql))
        except Exception:
            # If extension missing or already hypertable, ignore
            pass


def upsert_timescale(df: pd.DataFrame, engine: Engine, table: str) -> int:
    if df.empty:
        return 0
    _ensure_table(engine, table)

    # Use an INSERT ... ON CONFLICT upsert
    insert_sql = f"""
    INSERT INTO {table} (symbol, datetime, open, high, low, close, volume)
    VALUES (:symbol, :datetime, :open, :high, :low, :close, :volume)
    ON CONFLICT (symbol, datetime) DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume;
    """
    records = df.to_dict("records")
    with engine.begin() as conn:
        conn.execute(text(insert_sql), records)
    return len(records)


# --- CLI ----------------------------------------------------------------------

def save_csv(df: pd.DataFrame, symbol: str) -> str:
    os.makedirs(LIVE_DIR, exist_ok=True)
    path = os.path.join(LIVE_DIR, f"{symbol}_live.csv")
    df.to_csv(path, index=False)
    return path


def main():
    parser = argparse.ArgumentParser(description="Market data loader")
    parser.add_argument("symbol", help="Ticker symbol, e.g., AAPL")
    parser.add_argument("--provider", default="yf", choices=["yf"], help="Data provider (only 'yf' supported in this file)")
    parser.add_argument("--duration", default="5 D", help="Lookback period, e.g. '5 D', '1 Mo', '1 Y'")
    parser.add_argument("--bar-size", default="5 min", help="Bar size, e.g. '1 min', '5 min', '1 day'")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    if args.provider != "yf":
        raise SystemExit("Only Yahoo Finance (yf) provider is supported in this module.")

    print(f"[Loader] Provider=yf • Symbol={symbol}")
    df = fetch_yahoo(symbol, args.duration, args.bar_size)

    # Save CSV snapshot
    csv_path = save_csv(df, symbol)
    print(f"[Loader] Saved live data to: {csv_path}  (rows={len(df)})")

    # Upsert into TimescaleDB if URL provided
    if TS_URL:
        try:
            engine = create_engine(TS_URL, pool_pre_ping=True)
            count = upsert_timescale(df, engine, DEFAULT_TABLE)
            print(f"[TimescaleDB] Upserted {count} rows into table '{DEFAULT_TABLE}'.")
        except Exception as e:  # pragma: no cover
            print(f"[TimescaleDB] ERROR: {e}")
    else:
        print("[TimescaleDB] Skipped (TIMESCALE_URL not set).")


if __name__ == "__main__":
    # Allow running as module: python -m Projekt.my_trading_bot.data.market_data_api ...
    # Ensure package root on sys.path when executed directly
    if __package__ in (None, ""):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
    main()
