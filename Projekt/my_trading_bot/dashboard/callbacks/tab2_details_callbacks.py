import os
import tempfile
from functools import lru_cache
from threading import Lock

os.environ.setdefault("MPLBACKEND", "Agg")

import dash
from dash import html
from dash.dependencies import Input, Output
import matplotlib
import quantstats.reports as qsr

from dashboard.data_loader import (
    get_strategy_symbol_map,
    load_normalized_returns,
    result_file_path,
)

matplotlib.use("Agg", force=True)


_REPORT_CACHE_GUARD = Lock()


def _strategy_symbol_options(strategy: str | None):
    mapping = get_strategy_symbol_map()
    if not strategy or strategy not in mapping:
        return [], None, True

    options = [{"label": symbol, "value": symbol} for symbol in mapping[strategy]]
    default_value = mapping[strategy][0] if len(mapping[strategy]) == 1 else None
    return options, default_value, False


@dash.callback(
    Output("details-symbol-dropdown", "options"),
    Output("details-symbol-dropdown", "value"),
    Output("details-symbol-dropdown", "disabled"),
    Input("details-strategy-dropdown", "value"),
)
def update_symbol_dropdown(strategy):
    return _strategy_symbol_options(strategy)


@dash.callback(
    Output("quantstats-report", "children"),
    Input("details-strategy-dropdown", "value"),
    Input("details-symbol-dropdown", "value"),
)
def update_details(strategy, symbol):
    """Render QuantStats metrics table and report for the selected strategy/symbol."""
    if not strategy or not symbol:
        return html.Div("Bitte wähle zuerst eine Strategie und ein Symbol.", className="empty-state")

    try:
        content = _get_quantstats_report(strategy, symbol)
    except _NoDataAvailableError:
        return html.Div("Keine Daten für diese Kombination gefunden.", className="empty-state")
    except Exception as exc:  # pragma: no cover - defensive feedback path
        return html.Div(
            [
                html.P("Fehler beim Erstellen des QuantStats-Reports."),
                html.Pre(str(exc)),
            ],
            className="error-state",
        )

    return html.Iframe(
        srcDoc=content,
        style={"width": "100%", "height": "1800px", "border": "none"},
    )


class _NoDataAvailableError(RuntimeError):
    """Raised when no returns are available for the selected combination."""


def _get_quantstats_report(strategy: str, symbol: str) -> str:
    file_path = result_file_path(symbol, strategy)
    try:
        file_mtime = os.path.getmtime(file_path)
    except OSError:
        file_mtime = None

    with _REPORT_CACHE_GUARD:
        return _render_report_cached(strategy, symbol, file_mtime)


@lru_cache(maxsize=16)
def _render_report_cached(strategy: str, symbol: str, _file_mtime: float | None) -> str:
    returns = load_normalized_returns(symbol, strategy)
    if returns.empty:
        raise _NoDataAvailableError

    handle, temp_path = tempfile.mkstemp(suffix=".html")
    os.close(handle)

    try:
        qsr.html(
            returns,
            output=temp_path,
            title=f"Strategie Tearsheet: {strategy} – {symbol}",
            download_filename="quantstats_report.html",
        )
        with open(temp_path, "r", encoding="utf-8") as file:
            return file.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
