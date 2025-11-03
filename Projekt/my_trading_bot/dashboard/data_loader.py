from __future__ import annotations

import os
import sys
import json
import threading
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from glob import glob
from datetime import datetime, timezone

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
BOOTSTRAP_STATE_FILE = (ROOT / "Projekt" / "my_trading_bot" / "data" / "live_data" / ".bootstrap_state.json").resolve()
try:
    BOOTSTRAP_CACHE_TTL = int(os.environ.get("MARKET_BOOTSTRAP_CACHE_TTL", "900"))
except (TypeError, ValueError):
    BOOTSTRAP_CACHE_TTL = 900
BOOTSTRAP_PROVIDER = (os.environ.get("MARKET_BOOTSTRAP_PROVIDER", "yf").strip().lower() or "yf")

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
_bootstrap_lock = threading.RLock()
_bootstrap_thread: threading.Thread | None = None
_bootstrap_state: Dict[str, object] = {
    "state": "idle",
    "symbols": [],
    "message": "",
    "started_at": None,
    "finished_at": None,
    "last_success": None,
}
_bootstrap_warnings: list[str] = []
_emitted_warnings: set[str] = set()
BOOTSTRAP_DURATION = os.environ.get("MARKET_BOOTSTRAP_DURATION", "1 Y")
BOOTSTRAP_BAR_SIZE = os.environ.get("MARKET_BOOTSTRAP_BAR_SIZE", "1 day")


def _read_env_file() -> dict[str, str]:
    """Simple .env reader to pull bootstrap overrides without extra deps."""
    candidates = [
        PROJECT_ROOT / ".env",
        ROOT / ".env",
    ]
    data: dict[str, str] = {}
    for path in candidates:
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip().strip('"').strip("'")
        except OSError:
            continue
    return data


def _normalize_symbols(raw_symbols: Iterable[str]) -> Tuple[Tuple[str, ...], list[str]]:
    """Return sanitized symbols and validation warnings."""
    warnings: list[str] = []
    seen: set[str] = set()
    normalized: list[str] = []
    for token in raw_symbols:
        token = (token or "").strip()
        if not token:
            warnings.append("Encountered empty symbol entry; ignoring.")
            continue
        symbol = token.upper()
        if any(ch for ch in symbol if not (ch.isalnum() or ch in {".", "-", "_"})):
            warnings.append(f"Ignoring invalid symbol '{token}'.")
            continue
        if symbol in seen:
            warnings.append(f"Duplicate symbol '{symbol}' ignored.")
            continue
        seen.add(symbol)
        normalized.append(symbol)
    if not normalized:
        warnings.append("Bootstrap symbol list resolved to empty; skipping bootstrap.")
    return tuple(normalized), warnings


def _load_bootstrap_symbols() -> Tuple[Tuple[str, ...], list[str], str]:
    """Resolve bootstrap symbols from environment/.env/defaults."""
    env_file_values = _read_env_file()
    source = "default"
    raw = os.environ.get("MARKET_BOOTSTRAP_SYMBOLS")
    if raw:
        source = "env"
    else:
        raw = env_file_values.get("MARKET_BOOTSTRAP_SYMBOLS", "AAPL,GOOGL")
        if "MARKET_BOOTSTRAP_SYMBOLS" in env_file_values:
            source = ".env"
    candidates = [part for part in raw.replace(";", ",").split(",")]
    symbols, warnings = _normalize_symbols(candidates)
    return symbols, warnings, source


BOOTSTRAP_SYMBOLS, _bootstrap_warning_list, BOOTSTRAP_SOURCE = _load_bootstrap_symbols()
_bootstrap_warnings.extend(_bootstrap_warning_list)


def _load_cached_run() -> dict[str, object]:
    if not BOOTSTRAP_STATE_FILE.exists():
        return {}
    try:
        return json.loads(BOOTSTRAP_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cached_run(payload: dict[str, object]) -> None:
    try:
        BOOTSTRAP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BOOTSTRAP_STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[Bootstrap] WARNING: Unable to persist bootstrap cache ({exc}).")


def _should_skip_bootstrap(symbols: Iterable[str], duration: str, bar_size: str, provider: str, force: bool) -> bool:
    if force:
        return False
    meta = _load_cached_run()
    ts = meta.get("timestamp")
    cached_symbols = tuple(meta.get("symbols", []))
    if not ts or not cached_symbols:
        return False
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return False
    age = time.time() - ts
    if age > BOOTSTRAP_CACHE_TTL:
        return False
    if tuple(symbols) != cached_symbols:
        return False
    if duration != meta.get("duration") or bar_size != meta.get("bar_size"):
        return False
    if provider != str(meta.get("provider", "")).lower():
        return False
    return True


def _update_bootstrap_state(**kwargs: object) -> None:
    with _bootstrap_lock:
        _bootstrap_state.update(kwargs)


def get_bootstrap_status() -> str:
    state = _bootstrap_state.get("state", "idle")
    message = _bootstrap_state.get("message") or ""
    if state in {"running", "scheduled"}:
        return message or "Bootstrapping data…"
    last_success = _bootstrap_state.get("last_success")
    if last_success:
        return f"TimescaleDB (bootstrap @ {last_success})"
    if _bootstrap_warnings:
        return _bootstrap_warnings[-1]
    return message or "Idle"


def bootstrap_live_data(
    symbols: Iterable[str] | None = None,
    duration: str | None = None,
    bar_size: str | None = None,
    provider: str = "yf",
    *,
    force: bool = False,
) -> None:
    """Fetch live data for default symbols and upsert into the configured backend."""
    duration = duration or BOOTSTRAP_DURATION
    bar_size = bar_size or BOOTSTRAP_BAR_SIZE

    if symbols is None:
        resolved_symbols = BOOTSTRAP_SYMBOLS
    else:
        resolved_symbols, extra_warnings = _normalize_symbols(symbols)
        if extra_warnings:
            _bootstrap_warnings.extend(extra_warnings)
    for warning in _bootstrap_warnings:
        if warning in _emitted_warnings:
            continue
        print(f"[Bootstrap] WARNING: {warning}")
        _emitted_warnings.add(warning)
    if not resolved_symbols:
        _update_bootstrap_state(state="idle", message="Bootstrap skipped (no symbols).", symbols=[])
        return

    if provider.lower() != "yf":
        print(f"[Bootstrap] Unsupported provider '{provider}'. Skipping bootstrap.")
        _update_bootstrap_state(state="idle", message="Bootstrap skipped (provider).", symbols=[])
        return

    try:
        from Projekt.my_trading_bot.data import market_data_api
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[Bootstrap] Unable to import market data API: {exc}")
        return

    provider_key = provider.lower()
    if _should_skip_bootstrap(resolved_symbols, duration, bar_size, provider_key, force):
        cached = _load_cached_run()
        ts = cached.get("timestamp")
        stamp = (
            datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%MZ")
            if isinstance(ts, (int, float)) else "recently"
        )
        _update_bootstrap_state(
            state="cached",
            message=f"Bootstrap skipped (cache hit {stamp}).",
            symbols=list(resolved_symbols),
            last_success=stamp,
        )
        print(f"[Bootstrap] Using cached run from {stamp}; skipping fetch.")
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

    _update_bootstrap_state(
        state="running",
        message=f"Bootstrapping: {', '.join(resolved_symbols)}",
        symbols=list(resolved_symbols),
        started_at=time.time(),
    )
    print(f"[Bootstrap] Loading symbols {', '.join(resolved_symbols)} (duration={duration}, bar={bar_size})")
    success = False
    for symbol in resolved_symbols:
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
            success = True
        except Exception as exc:  # pragma: no cover - DB specific
            print(f"[Bootstrap] ERROR upserting {symbol}: {exc}")

    finished_at = time.time()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    _update_bootstrap_state(
        state="idle",
        message="Bootstrap complete." if success else "Bootstrap finished with issues.",
        symbols=list(resolved_symbols),
        finished_at=finished_at,
        last_success=stamp if success else _bootstrap_state.get("last_success"),
    )
    if success:
        _write_cached_run(
            {
                "timestamp": finished_at,
                "symbols": list(resolved_symbols),
                "duration": duration,
                "bar_size": bar_size,
                "provider": provider_key,
            }
        )


def _bootstrap_worker(
    symbols: Iterable[str] | None,
    duration: str | None,
    bar_size: str | None,
    provider: str,
    force: bool,
) -> None:
    try:
        bootstrap_live_data(
            symbols=symbols,
            duration=duration,
            bar_size=bar_size,
            provider=provider,
            force=force,
        )
    except Exception as exc:  # pragma: no cover
        print(f"[Bootstrap] ERROR: {exc}")
        _update_bootstrap_state(message=f"Bootstrap error: {exc}", state="idle")
    finally:
        _update_bootstrap_state(state="idle")


def schedule_bootstrap(
    *,
    symbols: Iterable[str] | None = None,
    duration: str | None = None,
    bar_size: str | None = None,
    force: bool | None = None,
) -> None:
    """Kick off bootstrap in the background (default symbols or custom list)."""
    provider = BOOTSTRAP_PROVIDER or "yf"
    target_duration = duration or BOOTSTRAP_DURATION
    target_bar_size = bar_size or BOOTSTRAP_BAR_SIZE

    if symbols is None:
        target_symbols = BOOTSTRAP_SYMBOLS
        extra_warnings: list[str] = []
    else:
        target_symbols, extra_warnings = _normalize_symbols(symbols)

    for warning in extra_warnings:
        if warning in _emitted_warnings:
            continue
        print(f"[Bootstrap] WARNING: {warning}")
        _emitted_warnings.add(warning)

    with _bootstrap_lock:
        global _bootstrap_thread
        eff_force = bool(force or os.environ.get("MARKET_BOOTSTRAP_FORCE"))
        if symbols is not None and force is None:
            eff_force = True  # always fetch freshly for ad-hoc requests

        if _bootstrap_thread and _bootstrap_thread.is_alive():
            print("[Bootstrap] Another job already running; request ignored.")
            _update_bootstrap_state(
                state="running",
                message="Bootstrap already running.",
            )
            return

        if not target_symbols:
            _update_bootstrap_state(
                state="idle",
                message="Bootstrap skipped (no symbols configured).",
                symbols=[],
            )
            return

        if _should_skip_bootstrap(
            target_symbols,
            target_duration,
            target_bar_size,
            provider,
            eff_force,
        ):
            cached = _load_cached_run()
            ts = cached.get("timestamp")
            stamp = (
                datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%MZ")
                if isinstance(ts, (int, float)) else "recently"
            )
            _update_bootstrap_state(
                state="cached",
                message=f"Bootstrap cached (last run {stamp}).",
                symbols=list(target_symbols),
                last_success=stamp,
            )
            print(f"[Bootstrap] Cache hit from {stamp}; background fetch skipped.")
            return

        _update_bootstrap_state(
            state="scheduled",
            message=f"Bootstrapping queued for {', '.join(target_symbols)}",
            symbols=list(target_symbols),
        )
        thread = threading.Thread(
            target=_bootstrap_worker,
            kwargs={
                "symbols": target_symbols,
                "duration": target_duration,
                "bar_size": target_bar_size,
                "provider": provider,
                "force": eff_force,
            },
            daemon=True,
            name="bootstrap-loader",
        )
        _bootstrap_thread = thread
        thread.start()
        print(
            f"[Bootstrap] Background fetch scheduled for {', '.join(target_symbols)} "
            f"(duration={target_duration}, bar={target_bar_size})."
        )

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
    state = _bootstrap_state.get("state", "idle")
    if state in {"scheduled", "running", "cached"}:
        return get_bootstrap_status()
    last_success = _bootstrap_state.get("last_success")
    warning = _bootstrap_warnings[-1] if _bootstrap_warnings else ""

    # Try DB
    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        if last_success:
            return f"TimescaleDB (bootstrap @ {last_success})"
        return "TimescaleDB"
    except Exception:
        pass

    # CSV fallback?
    symbols = _list_symbols_on_disk()
    if symbols:
        suffix = f" • {warning}" if warning else ""
        return f"CSV fallback{suffix}"
    return warning or "None"
