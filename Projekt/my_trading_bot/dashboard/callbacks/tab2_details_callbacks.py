# ==================== dashboard/callbacks/tab2_details_callbacks.py ====================

import os
import tempfile

import dash
from dash import html
from dash.dependencies import Input, Output

import quantstats.reports as qsr

from dashboard.data_loader import load_returns

@dash.callback(
    [Output("quantstats-metrics", "children"),
     Output("quantstats-report", "children")],
    [Input("details-strategy-dropdown", "value"),
     Input("details-symbol-dropdown", "value")]
)
def update_details(strategy, symbol):
    if not strategy or not symbol:
        return dash.no_update, dash.no_update

    returns = load_returns(symbol, strategy)
    if returns.empty:
        return html.Div("Keine Daten verfügbar."), html.Div()

    stats_df = qsr.metrics(returns, display=False)
    metrics_html = stats_df.to_html()

    metrics_content = html.Div([
        html.Iframe(
            srcDoc=metrics_html,
            style={"width": "100%", "height": "400px", "border": "none"},
        )
    ])

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".html")
        os.close(fd)

        qsr.html(
            returns,
            output=tmp_path,
            title=f"QuantStats Report: {strategy} - {symbol}",
            download_filename="quantstats-report.html",
        )

        with open(tmp_path, "r", encoding="utf-8") as report_file:
            report_html = report_file.read()

        report_content = html.Div(
            html.Iframe(
                srcDoc=report_html,
                style={"width": "100%", "height": "1600px", "border": "none"},
            )
        )
    except Exception as err:  # pragma: no cover - safeguard for runtime errors
        report_content = html.Div(
            [
                html.P("Fehler beim Laden der QuantStats-Grafiken."),
                html.Pre(str(err)),
            ]
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return metrics_content, report_content
