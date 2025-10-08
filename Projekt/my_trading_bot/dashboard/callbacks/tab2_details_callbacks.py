# ==================== dashboard/callbacks/tab2_details_callbacks.py ====================

import dash
from dash.dependencies import Input, Output
from dashboard.data_loader import load_returns
from dash import html
import plotly.graph_objects as go
import quantstats.reports as qsr

@dash.callback(
    [Output("quantstats-metrics", "children"),
     Output("quantstats-performance-graph", "figure")],
    [Input("details-strategy-dropdown", "value"),
     Input("details-symbol-dropdown", "value")]
)
def update_details(strategy, symbol):
    if not strategy or not symbol:
        return dash.no_update, dash.no_update

    returns = load_returns(symbol, strategy)
    if returns.empty:
        return "Keine Daten verfügbar.", go.Figure()

    stats_df = qsr.metrics(returns, display=False)
    metrics_html = stats_df.to_html()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=returns.index, y=(1 + returns).cumprod(), mode='lines', name='Kumulierte Rendite'))
    fig.update_layout(title=f"Kumulierte Rendite: {symbol} - {strategy}", xaxis_title="Datum", yaxis_title="Wert")

    return html.Div([
        html.Iframe(srcDoc=metrics_html, style={"width": "100%", "height": "400px", "border": "none"})
    ]), fig
