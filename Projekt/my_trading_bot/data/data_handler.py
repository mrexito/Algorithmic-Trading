"""CLI wrapper for market_data_api; fetches Yahoo data and upserts into TimescaleDB."""

from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import create_engine

try:  # pragma: no cover - runtime import guard
    from . import market_data_api
except ImportError:  # pragma: no cover
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(package_dir)
    for path in (package_dir, project_root):
        if path not in sys.path:
            sys.path.insert(0, path)
    from Projekt.my_trading_bot.data import market_data_api  # type: ignore  # noqa: E402


def _get_ts_config() -> tuple[str | None, str]:
    """Resolve Timescale connection info with environment overrides."""
    url = os.environ.get("TIMESCALE_URL", market_data_api.TS_URL)
    table = os.environ.get("TS_TABLE", market_data_api.DEFAULT_TABLE)
    return url, table


def main() -> None:
    parser = argparse.ArgumentParser(description="Market data loader")
    parser.add_argument("symbol", help="Ticker symbol, e.g., AAPL")
    parser.add_argument("--provider", default="yf", choices=["yf"], help="Data provider (only 'yf' supported)")
    parser.add_argument("--duration", default="1 Y", help="Lookback period, e.g. '5 D', '1 Mo', '1 Y'")
    parser.add_argument("--bar-size", default="1 day", help="Bar size, e.g. '1 min', '5 min', '1 day'")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    if args.provider != "yf":
        raise SystemExit("Only Yahoo Finance (yf) provider is supported in this module.")

    print(f"[Loader] Provider=yf • Symbol={symbol}")
    df = market_data_api.fetch_yahoo(symbol, args.duration, args.bar_size)

    csv_path = market_data_api.save_csv(df, symbol)
    print(f"[Loader] Saved live data to: {csv_path}  (rows={len(df)})")

    ts_url, table = _get_ts_config()
    if not ts_url:
        print("[TimescaleDB] Skipped (TIMESCALE_URL not set).")
        return

    try:
        engine = create_engine(ts_url, pool_pre_ping=True)
        count = market_data_api.upsert_timescale(df, engine, table)
        print(f"[TimescaleDB] Upserted {count} rows into table '{table}'.")
    except Exception as exc:  # pragma: no cover
        print(f"[TimescaleDB] ERROR: {exc}")


if __name__ == "__main__":
    main()
