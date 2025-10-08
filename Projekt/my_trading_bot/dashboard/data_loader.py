import os
import pickle
from typing import Optional

import pandas as pd
import yfinance as yf


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "data")
BENCHMARK_DIR = os.path.join(DATA_DIR, "benchmarks")


def _ensure_directories() -> None:
    """Stellt sicher, dass alle benoetigten Verzeichnisse existieren."""
    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(BENCHMARK_DIR, exist_ok=True)


def _benchmark_path(ticker: str) -> str:
    """Ermittelt den Dateipfad fuer den gegebenen Benchmark-Ticker."""
    _ensure_directories()
    safe_ticker = ticker.replace("/", "_")
    return os.path.join(BENCHMARK_DIR, f"{safe_ticker}.parquet")


def get_available_results():
    _ensure_directories()
    files = [f for f in os.listdir(RESULT_DIR) if f.endswith("_returns.pkl")]
    combos = []
    for f in files:
        name = f.replace("_returns.pkl", "")
        strat, symbol = name.split("_")
        combos.append((symbol, strat))
    return combos


def load_returns(symbol, strategy):
    _ensure_directories()
    file_path = os.path.join(RESULT_DIR, f"{strategy}_{symbol}_returns.pkl")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    return pd.Series()


def _prepare_daily_returns(series: pd.Series) -> pd.Series:
    """Formt Roh-Renditen in eine taegliche Rendite-Zeitreihe um."""
    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index, errors="coerce")
    series = series.dropna().sort_index()

    returns = series.pct_change().fillna(0.0)
    returns = returns.groupby(returns.index.normalize()).apply(lambda r: (1.0 + r).prod() - 1.0)
    returns = returns.asfreq("D", fill_value=0.0)
    try:
        returns.index.freq = pd.tseries.frequencies.to_offset("D")
    except Exception:
        pass
    returns.name = "returns"
    return returns


def fetch_and_cache_benchmark(ticker: str, start: Optional[str] = None, end: Optional[str] = None) -> pd.Series:
    """Lädt Benchmarkdaten via yfinance, verarbeitet sie und speichert sie im Cache."""
    path = _benchmark_path(ticker)

    data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if data is None or data.empty:
        raise ValueError(f"Keine Benchmarkdaten fuer {ticker} verfügbar.")

    if isinstance(data.columns, pd.MultiIndex):
        try:
            adj_close = data.xs("Adj Close", axis=1, level=0)
        except KeyError as exc:
            raise ValueError("Adj Close Spalte nicht gefunden.") from exc
        if isinstance(adj_close, pd.DataFrame):
            adj_close = adj_close.iloc[:, 0]
    else:
        if "Adj Close" not in data.columns:
            raise ValueError("Adj Close Spalte nicht gefunden.")
        adj_close = data["Adj Close"]

    adj_close = pd.to_numeric(adj_close, errors="coerce").dropna()
    returns = _prepare_daily_returns(adj_close)

    returns.to_frame().to_parquet(path, index=True)
    return returns


def load_cached_benchmark(ticker: str) -> Optional[pd.Series]:
    """Lädt einen bereits vorhandenen Benchmark aus dem lokalen Cache."""
    path = _benchmark_path(ticker)
    if not os.path.exists(path):
        return None

    series = pd.read_parquet(path).squeeze("columns")
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index, errors="coerce")
    series = series.sort_index().astype(float)
    try:
        series.index.freq = pd.tseries.frequencies.to_offset("D")
    except Exception:
        pass
    series.name = "returns"
    return series


def get_benchmark_returns(ticker: str, index: Optional[pd.DatetimeIndex] = None) -> Optional[pd.Series]:
    """Gibt taegliche Benchmark-Renditen zurueck, optional auf einen Index ausgerichtet."""
    series = load_cached_benchmark(ticker)
    if series is None:
        try:
            series = fetch_and_cache_benchmark(ticker)
        except Exception:
            return None

    if index is not None:
        index = pd.DatetimeIndex(index)
        series = series.reindex(index, fill_value=0.0)
        try:
            series.index.freq = pd.tseries.frequencies.to_offset("D")
        except Exception:
            pass

    return series
