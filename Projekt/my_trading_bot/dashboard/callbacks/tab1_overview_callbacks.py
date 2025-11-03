# ==================== dashboard/callbacks/tab1_overview_callbacks.py ====================
"""Callbacks powering the overview tab with metrics table and return curves."""

import re
import time

import dash
from dash.dependencies import Input, Output, State
from dashboard.data_loader import (
    get_available_results,
    load_returns,
    schedule_bootstrap,
)
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


@dash.callback(
    Output("overview-symbol-dropdown", "options"),
    Output("overview-strategy-dropdown", "options"),
    Output("bootstrap-symbol-message", "children"),
    Output("bootstrap-symbol-input", "value"),
    Output("bootstrap-requested-symbols", "data"),
    Output("bootstrap-reload-store", "data"),
    Input("backend-status-ivl", "n_intervals"),
    Input("bootstrap-symbol-button", "n_clicks"),
    State("bootstrap-symbol-input", "value"),
    State("bootstrap-requested-symbols", "data"),
    prevent_initial_call=False,
)
def refresh_symbol_options(_tick, n_clicks, raw_symbols, requested_state):
    """Refresh dropdown options and optionally trigger a data bootstrap for new symbols."""
    triggered = dash.callback_context.triggered[0]["prop_id"] if dash.callback_context.triggered else ""
    message = dash.no_update
    reset_value = dash.no_update
    reload_trigger = dash.no_update
    requested_symbols = requested_state or []
    requested_update = dash.no_update

    if triggered.startswith("bootstrap-symbol-button") and n_clicks:
        tokens = []
        if raw_symbols:
            tokens = [
                token.strip().upper()
                for token in re.split(r"[,\s]+", raw_symbols)
                if token.strip()
            ]
        if not tokens:
            message = "Bitte mindestens ein gültiges Symbol angeben."
        else:
            unique_tokens = sorted(set(tokens))
            schedule_bootstrap(symbols=tokens, force=True)
            joined = ", ".join(unique_tokens)
            message = f"Bootstrap ausgelöst für {joined}."
            reset_value = ""
            requested_update = unique_tokens

    results = get_available_results()
    symbols = sorted({sym for sym, _ in results})
    strategies = sorted({strat for _, strat in results})

    symbol_options = [{"label": sym, "value": sym} for sym in symbols]
    strategy_options = [{"label": strat, "value": strat} for strat in strategies]

    if requested_symbols and set(requested_symbols).issubset(set(symbols)):
        if message is dash.no_update:
            message = f"Daten geladen: {', '.join(requested_symbols)}."
        reload_trigger = time.time()
        requested_update = []

    return (
        symbol_options,
        strategy_options,
        message,
        reset_value,
        requested_update,
        reload_trigger,
    )
