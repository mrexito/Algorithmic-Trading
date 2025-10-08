# ==================== dashboard/callbacks/tab2_details_callbacks.py ====================

import dash
from dash.dependencies import Input, Output
from dashboard.data_loader import load_returns
from dash import html
import quantstats.reports as qsr
import tempfile
import os

@dash.callback(
    Output("quantstats-report-container", "children"),
    [
        Input("details-strategy-dropdown", "value"),
        Input("details-symbol-dropdown", "value"),
    ],
)
def update_details(strategy, symbol):
    if not strategy or not symbol:
        return dash.no_update

    returns = load_returns(symbol, strategy)
    if returns.empty:
        return html.Div("Keine Daten verfügbar.")

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
        temp_path = tmp_file.name

    try:
        qsr.html(
            returns,
            output=temp_path,
            title=f"QuantStats Report: {strategy} - {symbol}",
            download_filename=f"quantstats-{strategy}-{symbol}.html",
            strategy_title=strategy,
        )
        with open(temp_path, "r", encoding="utf-8") as f:
            report_html = f.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return html.Iframe(
        srcDoc=report_html,
        style={
            "width": "100%",
            "height": "2000px",
            "border": "none",
        },
    )
