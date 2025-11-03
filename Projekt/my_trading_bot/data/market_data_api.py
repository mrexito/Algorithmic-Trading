from __future__ import annotations

import os
from pathlib import Path
import time
from datetime import datetime, timezone
from typing import Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Optional import of yfinance
try:
    import yfinance as yf
except Exception as e:  # pragma: no cover
    yf = None

# --- Configuration ---------------------------------------------------------
TS_URL: str | None = os.environ.get("TIMESCALE_URL")
DEFAULT_TABLE = os.environ.get("TS_TABLE", "ohlcv")
DATA_DIR = Path(__file__).resolve().parents[2] / "Projekt" / "my_trading_bot" / "data" / "live_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_COLS = ["datetime", "open", "high", "low", "close", "volume", "symbol"]

# --- Helpers ---------------------------------------------------------------

def _map_yf_params(duration: str, bar_size: str) -> Tuple[str, str]:
    """Map UI-friendly duration/bar_size to yfinance period/interval."""
    duration = (duration or "").strip().lower()
    bar_size = (bar_size or "").strip().lower()

    period_map = {
        "1 d": "1d",
        "2 d": "2d",
        "5 d": "5d",
        "1 mo": "1mo",
        "3 mo": "3mo",
        "6 mo": "6mo",
        "1 y": "1y",
    }
    interval_map = {
        "1 min": "1m",
        "2 min": "2m",
        "5 min": "5m",
        "15 min": "15m",
        "30 min": "30m",
        "60 min": "60m",
        "1 day": "1d",
    }

    period = period_map.get(duration, "5d")
    interval = interval_map.get(bar_size, "5m")
    return period, interval

# --- Public API ------------------------------------------------------------

def fetch_yahoo(
    symbol: str,
    duration: str,
    bar_size: str,
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> pd.DataFrame:
    """Fetch OHLCV from Yahoo Finance and normalize columns.

    Returns a DataFrame with columns: datetime, open, high, low, close, volume, symbol
    """
    if yf is None:
        raise RuntimeError("yfinance is not installed. Please `pip install yfinance`." )

    period, interval = _map_yf_params(duration, bar_size)

    if max_attempts < 1:
        max_attempts = 1

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            df = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
            )
            break
        except Exception as exc:
            last_exc = exc
            if attempt >= max_attempts:
                raise RuntimeError(f"Failed to fetch data for {symbol}: {exc}") from exc
            delay = base_delay * (backoff_factor ** (attempt - 1))
            time.sleep(delay)
    else:
        # Should never hit but keeps type checker happy
        df = pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame(columns=REQUIRED_COLS)

    # Handle multi-index columns for multiple tickers; also single-ticker shape
    if isinstance(df.columns, pd.MultiIndex):
        # e.g. columns like ('Open','AAPL')
        df.columns = [f"{c[0].lower()}" for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    # Rename Yahoo's columns to our standard if needed
    rename_map = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "adj close": "close",  # use close if present; adj close fallback is uncommon for intraday
        "volume": "volume",
    }
    df = df.rename(columns=rename_map)

    # yfinance may expose both Close and Adj Close -> drop duplicates after renaming
    df = df.loc[:, ~df.columns.duplicated()]

    # yfinance may expose both Close and Adj Close -> drop duplicates after renaming
    df = df.loc[:, ~df.columns.duplicated()]

    # Reset index to get datetime column
    df = df.reset_index().rename(columns={"index": "datetime", "Datetime": "datetime", "Date": "datetime"})

    # Ensure datetime tz-aware UTC
    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    else:
        if df["datetime"].dt.tz is None:
            df["datetime"] = df["datetime"].dt.tz_localize(timezone.utc)
        else:
            df["datetime"] = df["datetime"].dt.tz_convert(timezone.utc)

    # Add symbol column
    df["symbol"] = symbol.upper()

    # Keep only required columns if present
    keep = [c for c in ["datetime","open","high","low","close","volume","symbol"] if c in df.columns]
    df = df[keep]

    # Validate required columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise RuntimeError(f"Unexpected yfinance columns; missing {missing}. Got: {list(df.columns)}")

    # Sort and drop potential duplicates
    df = df.sort_values("datetime").drop_duplicates(subset=["symbol","datetime"], keep="last").reset_index(drop=True)

    return df


def save_csv(df: pd.DataFrame, symbol: str) -> str:
    """Save the dataframe to a CSV snapshot and return its path."""
    symbol = symbol.upper()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = DATA_DIR / f"{symbol}_live.csv"
    df.to_csv(path, index=False)
    return str(path)


def upsert_timescale(df: pd.DataFrame, engine: Engine, table: str = DEFAULT_TABLE) -> int:
    """UPSERT rows into TimescaleDB. Requires unique constraint on (symbol, datetime)."""
    if df.empty:
        return 0

    # Ensure target table exists with appropriate schema
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
    with engine.begin() as conn:
        conn.execute(text(create_sql))
        # Convert df to records
        records = df[["symbol","datetime","open","high","low","close","volume"]].to_dict("records")
        # Build parameterized upsert
        upsert_sql = text(
            f"""
            INSERT INTO {table} (symbol, datetime, open, high, low, close, volume)
            VALUES (:symbol, :datetime, :open, :high, :low, :close, :volume)
            ON CONFLICT (symbol, datetime) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
            """
        )
        conn.execute(upsert_sql, records)

    return len(df)
