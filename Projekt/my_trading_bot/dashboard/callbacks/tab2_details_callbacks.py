import os
import tempfile

import dash
from dash import html
from dash.dependencies import Input, Output
import quantstats.reports as qsr

from dashboard.data_loader import (
    get_strategy_symbol_map,
    load_returns,
    normalize_returns,
)


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
    if not strategy or not symbol:
        return html.Div("Bitte wähle zuerst eine Strategie und ein Symbol.", className="empty-state")

    raw = load_returns(symbol, strategy)
    returns = normalize_returns(raw)
    if returns.empty:
        return html.Div("Keine Daten für diese Kombination gefunden.", className="empty-state")

    temp_path = None
    try:
        handle, temp_path = tempfile.mkstemp(suffix=".html")
        os.close(handle)
        qsr.html(
            returns,
            output=temp_path,
            title=f"Strategie Tearsheet: {strategy} – {symbol}",
            download_filename="quantstats_report.html",
        )
        with open(temp_path, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception as exc:  # pragma: no cover - defensive feedback path
        return html.Div(
            [
                html.P("Fehler beim Erstellen des QuantStats-Reports."),
                html.Pre(str(exc)),
            ],
            className="error-state",
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return html.Iframe(
        srcDoc=content,
        style={"width": "100%", "height": "1800px", "border": "none"},
    )
