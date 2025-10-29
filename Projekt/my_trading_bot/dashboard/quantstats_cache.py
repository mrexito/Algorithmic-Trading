"""Utilities for building and caching QuantStats tearsheets."""
from __future__ import annotations

import atexit
import logging
import os
import tempfile
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Dict, Tuple

import quantstats.reports as qsr

from dashboard.data_loader import (
    get_available_results,
    load_returns,
    normalize_returns,
    result_file_path,
)


_LOGGER = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent
_CACHE_DIR = _BASE_DIR / "cache" / "quantstats"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_REFRESH_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="quantstats-cache")
_PENDING_REFRESHES: Dict[Tuple[str, str], Future] = {}
_CACHE_LOCK = Lock()


class NoDataAvailableError(RuntimeError):
    """Raised when no returns are available for the selected combination."""


def shutdown_executor():
    _REFRESH_EXECUTOR.shutdown(wait=False)


def _cache_file(strategy: str, symbol: str) -> Path:
    safe_strategy = strategy.replace(os.sep, "_")
    safe_symbol = symbol.replace(os.sep, "_")
    return _CACHE_DIR / f"{safe_strategy}__{safe_symbol}.html"


@lru_cache(maxsize=32)
def _load_cached_content(strategy: str, symbol: str, cache_mtime: float) -> str:
    cache_path = _cache_file(strategy, symbol)
    with cache_path.open("r", encoding="utf-8") as file:
        return file.read()


def _read_cache(strategy: str, symbol: str, cache_mtime: float) -> str:
    return _load_cached_content(strategy, symbol, cache_mtime)


def _is_cache_valid(cache_path: Path, data_mtime: float | None) -> bool:
    if data_mtime is None:
        return False
    if not cache_path.exists():
        return False
    try:
        return cache_path.stat().st_mtime >= data_mtime
    except FileNotFoundError:
        return False


def _render_report(strategy: str, symbol: str, cache_path: Path) -> str:
    raw_returns = load_returns(symbol, strategy)
    returns = normalize_returns(raw_returns)
    if returns.empty:
        raise NoDataAvailableError

    handle, temp_path = tempfile.mkstemp(suffix=".html")
    os.close(handle)

    try:
        qsr.html(
            returns,
            output=temp_path,
            title=f"Strategie Tearsheet: {strategy} – {symbol}",
            download_filename="quantstats_report.html",
            figfmt="png",
        )

        os.replace(temp_path, cache_path)
        _load_cached_content.cache_clear()
        return _read_cache(strategy, symbol, cache_path.stat().st_mtime)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _generate_and_store(strategy: str, symbol: str) -> None:
    cache_path = _cache_file(strategy, symbol)
    try:
        _render_report(strategy, symbol, cache_path)
    except NoDataAvailableError:
        if cache_path.exists():
            try:
                cache_path.unlink()
                _load_cached_content.cache_clear()
            except OSError:
                pass
    except Exception as exc:  # pragma: no cover - defensive logging path
        _LOGGER.exception("Failed to precompute QuantStats report for %s/%s: %s", strategy, symbol, exc)


def _schedule_refresh(strategy: str, symbol: str) -> None:
    key = (strategy, symbol)
    with _CACHE_LOCK:
        future = _PENDING_REFRESHES.get(key)
        if future and not future.done():
            return

        def task() -> None:
            try:
                _generate_and_store(strategy, symbol)
            finally:
                with _CACHE_LOCK:
                    _PENDING_REFRESHES.pop(key, None)

        _PENDING_REFRESHES[key] = _REFRESH_EXECUTOR.submit(task)


def get_report(strategy: str, symbol: str) -> str:
    data_path = Path(result_file_path(symbol, strategy))
    if not data_path.exists():
        raise NoDataAvailableError

    try:
        data_mtime = data_path.stat().st_mtime
    except FileNotFoundError:
        raise NoDataAvailableError from None

    cache_path = _cache_file(strategy, symbol)

    if _is_cache_valid(cache_path, data_mtime):
        try:
            cache_mtime = cache_path.stat().st_mtime
        except FileNotFoundError:
            cache_mtime = None
        else:
            return _read_cache(strategy, symbol, cache_mtime)

    if cache_path.exists():
        try:
            cached_mtime = cache_path.stat().st_mtime
        except FileNotFoundError:
            cached_mtime = None
        else:
            _schedule_refresh(strategy, symbol)
            return _read_cache(strategy, symbol, cached_mtime)

    # Cache missing or outdated without usable fallback -> build synchronously
    return _render_report(strategy, symbol, cache_path)


def preload_existing_reports() -> None:
    combos = defaultdict(list)
    for symbol, strategy in get_available_results():
        combos[strategy].append(symbol)

    for strategy, symbols in combos.items():
        for symbol in symbols:
            data_path = Path(result_file_path(symbol, strategy))
            if not data_path.exists():
                continue
            try:
                data_mtime = data_path.stat().st_mtime
            except FileNotFoundError:
                continue
            cache_path = _cache_file(strategy, symbol)
            if _is_cache_valid(cache_path, data_mtime):
                continue
            _schedule_refresh(strategy, symbol)


atexit.register(shutdown_executor)
