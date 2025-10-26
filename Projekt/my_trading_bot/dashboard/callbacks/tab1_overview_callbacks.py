# ==================== dashboard/callbacks/tab1_overview_callbacks.py ====================
"""Callbacks powering the overview tab with metrics table and return curves."""

import dash
from dash.dependencies import Input, Output
from dashboard.data_loader import load_returns
from dash import html
import plotly.graph_objs as go
import quantstats.stats as qs_stats
import pandas as pd


@dash.callback(
    [
        Output("performance-table", "children"),
        Output("overview-comparison-graph", "figure"),
    ],
    [
        Input("overview-symbol-dropdown", "value"),
        Input("overview-strategy-dropdown", "value"),
    ],
)
def update_overview_tab(selected_symbols, selected_strategies):
    """Render performance table and cumulative plots for the selected filters."""
    if not selected_symbols or not selected_strategies:
        return dash.no_update, dash.no_update

    rows = []
    fig = go.Figure()

    for symbol in selected_symbols:
        for strategy in selected_strategies:
            returns = load_returns(symbol, strategy)
            if not returns.empty:
                returns.index = pd.to_datetime(returns.index)
                returns = returns.asfreq("B").fillna(0)

                def get_metric(metric_func):
                    try:
                        val = metric_func(returns)
                        return f"{val:.5f}" if val is not None else "N/A"
                    except Exception:
                        return "N/A"

                rows.append(
                    html.Tr(
                        [
                            html.Td(symbol),
                            html.Td(strategy),
                            html.Td(get_metric(qs_stats.consecutive_wins)),
                            html.Td(get_metric(qs_stats.consecutive_losses)),
                            html.Td(get_metric(qs_stats.avg_return)),
                            html.Td(get_metric(qs_stats.avg_loss)),
                            html.Td(get_metric(qs_stats.win_rate)),
                            html.Td(get_metric(qs_stats.win_loss_ratio)),
                            html.Td(get_metric(qs_stats.probabilistic_sharpe_ratio)),
                            html.Td(get_metric(qs_stats.profit_factor)),
                        ]
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=returns.index,
                        y=(1 + returns).cumprod(),
                        mode="lines",
                        name=f"{symbol}-{strategy}",
                    )
                )

    table = html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Symbol"),
                        html.Th("Strategie"),
                        html.Th("consecutive_wins"),
                        html.Th("consecutive_losses"),
                        html.Th("avg_return"),
                        html.Th("avg_loss"),
                        html.Th("win_rate"),
                        html.Th("win_loss_ratio"),
                        html.Th("probabilistic_sharpe_ratio"),
                        html.Th("profit_factor"),
                    ]
                )
            ),
            html.Tbody(rows),
        ]
    )

    fig.update_layout(
        title="Kumulierte Rendite", xaxis_title="Datum", yaxis_title="Wert"
    )
    return table, fig
