"""Utility entry point for executing all strategies and storing their returns."""

from __future__ import annotations

import importlib.util
import inspect
import os
import pickle
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Tuple, Type
import sys

import backtrader as bt
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import PREDEFINED_SYMBOLS, CAPITAL, COMMISSION
from data.market_data_api import fetch_yahoo, save_csv, upsert_timescale, DATA_DIR as LIVE_DATA_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "data", "historical_prices")
STRATEGY_DIR = Path(BASE_DIR) / "strategies"

DEFAULT_DURATION = os.environ.get("BACKTEST_DURATION", "5 Y")
DEFAULT_BAR_SIZE = os.environ.get("BACKTEST_BAR_SIZE", "1 day")
TS_URL = os.environ.get("TIMESCALE_URL")
DEFAULT_TABLE = os.environ.get("TS_TABLE", "ohlcv")

_STRATEGY_NAME_MAP = {
    "ai": "AI",
    "bollinger": "BOLLINGER",
    "dtw": "DTW",
    "horizontal_pattern": "HORIZONTAL",
    "macd": "MACD",
    "rsi": "RSI",
    "sma": "SMA",
    "zigzag": "ZIGZAG",
}

_engine: Engine | None = None


def _get_engine() -> Engine | None:
    """Create a reusable TimescaleDB engine if configured."""
    global _engine
    if _engine is not None:
        return _engine
    if not TS_URL:
        return None
    try:
        _engine = create_engine(TS_URL, pool_pre_ping=True)
    except Exception as exc:
        print(f"[Backtest] WARNING: TimescaleDB unavailable ({exc}); continuing without DB.")
        _engine = None
    return _engine


def _discover_strategies() -> Dict[str, Type[bt.Strategy]]:
    """Import strategy classes from the strategies/ folder dynamically."""
    strategies: Dict[str, Type[bt.Strategy]] = {}
    for path in STRATEGY_DIR.glob("*_strategy.py"):
        stem = path.stem
        key = stem.replace("_strategy", "")
        name = _STRATEGY_NAME_MAP.get(key, key.upper())
        try:
            spec = importlib.util.spec_from_file_location(f"strategies.{stem}", path)
            if spec is None or spec.loader is None:
                print(f"[Backtest] WARNING: Unable to load {path.name}; skipping.")
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module  # ensure module is registered for Backtrader introspection
            spec.loader.exec_module(module)  # type: ignore[arg-type]
        except Exception as exc:
            print(f"[Backtest] WARNING: Failed to import {path.name}: {exc}")
            continue

        cls = None
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, bt.Strategy) and obj is not bt.Strategy:
                cls = obj
                break

        if cls is None:
            print(f"[Backtest] WARNING: No Strategy subclass found in {path.name}; skipping.")
            continue

        strategies[name] = cls
    return strategies


def _load_prices_from_db(symbol: str, engine: Engine) -> pd.DataFrame:
    """Load OHLCV prices for the last 5 years from TimescaleDB."""
    start = datetime.now(timezone.utc) - timedelta(days=365 * 5 + 5)
    sql = text(
        f"""
        SELECT datetime, open, high, low, close, volume
        FROM {DEFAULT_TABLE}
        WHERE symbol = :symbol AND datetime >= :start
        ORDER BY datetime
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"symbol": symbol, "start": start})
    if not df.empty:
        df = df.set_index("datetime")
    return df


def _price_dataframe(symbol: str, fetched_df: pd.DataFrame, engine: Engine | None) -> pd.DataFrame:
    """Return the price DataFrame used for backtesting, preferring DB if available."""
    if engine:
        try:
            db_df = _load_prices_from_db(symbol, engine)
            if not db_df.empty:
                return db_df
        except Exception as exc:
            print(f"[Backtest] WARNING: Could not load {symbol} from DB ({exc}); falling back to fetched CSV.")

    # Fallback to fetched dataframe
    return fetched_df.set_index("datetime")


def _cleanup_artifacts() -> None:
    """Remove previous live CSV snapshots and result pickles to ensure fresh runs."""
    removed_hist_csv = 0
    for path in Path(DATA_DIR).glob("*.csv"):
        try:
            path.unlink()
            removed_hist_csv += 1
        except OSError:
            pass

    removed_live_csv = 0
    for path in LIVE_DATA_DIR.glob("*.csv"):
        try:
            path.unlink()
            removed_live_csv += 1
        except OSError:
            pass

    removed_pkl = 0
    for path in Path(RESULT_DIR).glob("*.pkl"):
        try:
            path.unlink()
            removed_pkl += 1
        except OSError:
            pass

    removed_pycache = 0
    for path in Path(BASE_DIR).rglob("__pycache__"):
        try:
            shutil.rmtree(path)
            removed_pycache += 1
        except OSError:
            pass

    if removed_hist_csv or removed_live_csv or removed_pkl or removed_pycache:
        print(
            "[Backtest] Cleaned "
            f"{removed_hist_csv} historical CSVs, "
            f"{removed_live_csv} live CSVs, "
            f"{removed_pkl} result pickles, "
            f"{removed_pycache} __pycache__ directories."
        )


def run_backtests():
    """Fetch 5Y data, persist to TimescaleDB/CSV, and backtest every strategy on every symbol."""
    strategies = _discover_strategies()
    if not strategies:
        print("[Backtest] ERROR: No strategies discovered; aborting.")
        return

    engine = _get_engine()

    os.makedirs(RESULT_DIR, exist_ok=True)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    LIVE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup_artifacts()

    for symbol in PREDEFINED_SYMBOLS:
        df = fetch_yahoo(symbol, DEFAULT_DURATION, DEFAULT_BAR_SIZE)
        if df.empty:
            print(f"[Backtest] WARNING: No market data for {symbol}; skipping.")
            continue

        # Cache CSV snapshot to match historical_prices format
        save_csv(df, symbol)
        csv_path = Path(DATA_DIR) / f"{symbol}.csv"
        df.to_csv(csv_path, index=False)

        if engine is not None:
            try:
                rows = upsert_timescale(df, engine, DEFAULT_TABLE)
                print(f"[Backtest] Upserted {rows} rows for {symbol} into '{DEFAULT_TABLE}'.")
            except Exception as exc:
                print(f"[Backtest] WARNING: Failed to upsert {symbol} into DB ({exc}).")

        price_df = _price_dataframe(symbol, df, engine)
        if price_df.empty:
            print(f"[Backtest] WARNING: No price data available for {symbol}; skipping strategies.")
            continue

        for strat_name, strat_class in strategies.items():
            cerebro = bt.Cerebro()
            data = bt.feeds.PandasData(dataname=price_df)
            cerebro.adddata(data)
            cerebro.addstrategy(strat_class)
            # Position sizing: default to 5% of capital per trade; adjust if needed
            cerebro.addsizer(bt.sizers.PercentSizer, percents=5)
            cerebro.broker.set_cash(CAPITAL)
            cerebro.broker.setcommission(commission=COMMISSION)
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
            try:
                results = cerebro.run()
            except Exception as exc:
                print(f"[Backtest] WARNING: Strategy {strat_name} failed on {symbol}: {exc}")
                continue

            returns = results[0].analyzers.timereturn.get_analysis()
            returns_series = pd.Series(returns)

            filename = f"{strat_name}_{symbol}_returns.pkl"
            with open(os.path.join(RESULT_DIR, filename), "wb") as f:
                pickle.dump(returns_series, f)


if __name__ == "__main__":
    run_backtests()
