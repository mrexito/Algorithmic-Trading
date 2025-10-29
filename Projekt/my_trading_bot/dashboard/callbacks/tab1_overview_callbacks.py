import copy

import dash
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import quantstats.stats as qs_stats
from dash import dash_table, html
from dash.dependencies import Input, Output, State

from dashboard.data_loader import load_normalized_returns


_METRICS = (
    ("CAGR (%)", lambda r: qs_stats.cagr(r) * 100),
    ("Sharpe Ratio", lambda r: qs_stats.sharpe(r, periods=252)),
    ("Max Drawdown (%)", lambda r: qs_stats.max_drawdown(r) * 100),
    ("Trefferquote (%)", lambda r: qs_stats.win_rate(r) * 100),
    ("Profit-Faktor", qs_stats.profit_factor),
    ("Ø Tagesrendite (%)", lambda r: qs_stats.avg_return(r) * 100),
    ("Ø Verlust (%)", lambda r: qs_stats.avg_loss(r) * 100),
    ("Gewinnserie", qs_stats.consecutive_wins),
    ("Verlustserie", qs_stats.consecutive_losses),
)


def _safe_value(metric, returns):
    try:
        value = metric(returns)
    except Exception:
        return None

    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        return None

    if isinstance(value, (float, np.floating)) and (np.isnan(value) or np.isinf(value)):
        return None

    return value


def _format_value(value):
    if value is None:
        return "–"
    if isinstance(value, (float, np.floating)):
        return f"{value:.2f}"
    return str(value)


@dash.callback(
    Output("performance-table", "children"),
    Output("overview-comparison-graph", "figure"),
    Input("overview-symbol-dropdown", "value"),
    Input("overview-strategy-dropdown", "value"),
    State("overview-comparison-graph", "figure"),
)
def update_overview_tab(
    selected_symbols,
    selected_strategies,
    existing_figure,
):
    ctx = dash.callback_context
    triggered_id = getattr(ctx, "triggered_id", None)
    if triggered_id is None and ctx.triggered:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id in {"overview-zoom-in", "overview-zoom-out", "overview-zoom-reset"}:
        if not existing_figure:
            return dash.no_update, dash.no_update

        adjusted = _adjust_zoom(existing_figure, triggered_id)
        if adjusted is None:
            return dash.no_update, dash.no_update

        return dash.no_update, adjusted

    if not selected_symbols or not selected_strategies:
        return dash.no_update, dash.no_update

    table_rows = []
    figure = go.Figure()

    for symbol in selected_symbols:
        for strategy in selected_strategies:
            returns = load_normalized_returns(symbol, strategy)
            if returns.empty:
                continue

            metrics = {name: _format_value(_safe_value(func, returns)) for name, func in _METRICS}
            table_rows.append({
                "Symbol": symbol,
                "Strategie": strategy,
                **metrics,
            })

            cumulative = (1 + returns).cumprod()
            figure.add_trace(
                go.Scatter(
                    x=cumulative.index,
                    y=cumulative.values,
                    mode="lines",
                    name=f"{symbol} – {strategy}",
                )
            )

    if not table_rows:
        empty_message = html.Div("Für die Auswahl liegen keine Daten vor.", className="empty-state")
        figure.update_layout(
            template="plotly_white",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                {
                    "text": "Keine Daten verfügbar",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 16, "color": "#6b7280"},
                }
            ],
        )
        return empty_message, figure

    performance_table = dash_table.DataTable(
        data=table_rows,
        columns=[{"name": column, "id": column} for column in table_rows[0].keys()],
        style_table={"overflowX": "auto"},
        style_cell={
            "padding": "8px",
            "fontSize": "14px",
            "textAlign": "center",
        },
        style_header={
            "backgroundColor": "#2563eb",
            "color": "white",
            "fontWeight": "600",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f4f5f9"},
        ],
    )

    figure.update_layout(
        title="Kumulierte Rendite",
        xaxis_title="Datum",
        yaxis_title="Wachstum",
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="Kombination",
        uirevision="overview-graph",
    )

    return performance_table, figure


def _adjust_zoom(figure, action):
    if not figure or not figure.get("data"):
        return None

    x_values = []
    for trace in figure.get("data", []):
        x_values.extend(trace.get("x", []))

    if not x_values:
        return None

    series = pd.to_datetime(pd.Series(x_values))
    series = series.dropna().sort_values()
    if series.empty:
        return None

    full_start = series.iloc[0]
    full_end = series.iloc[-1]

    if full_start == full_end:
        return None

    layout = figure.get("layout", {})
    current_range = layout.get("xaxis", {}).get("range")
    if current_range and len(current_range) == 2:
        current_start = pd.to_datetime(current_range[0])
        current_end = pd.to_datetime(current_range[1])
    else:
        current_start, current_end = full_start, full_end

    if action == "overview-zoom-reset":
        new_start, new_end = full_start, full_end
    else:
        span = max(current_end - current_start, pd.Timedelta(0))
        if span == pd.Timedelta(0):
            span = full_end - full_start
        factor = 0.7 if action == "overview-zoom-in" else 1.3
        new_span = span * factor
        full_span = full_end - full_start
        if new_span >= full_span:
            new_start, new_end = full_start, full_end
        else:
            center = current_start + span / 2
            half_span = new_span / 2
            new_start = center - half_span
            new_end = center + half_span

            if new_start < full_start:
                shift = full_start - new_start
                new_start += shift
                new_end += shift
            if new_end > full_end:
                shift = new_end - full_end
                new_start -= shift
                new_end -= shift

            new_start = max(new_start, full_start)
            new_end = min(new_end, full_end)

    if new_start >= new_end:
        new_start, new_end = full_start, full_end

    updated = copy.deepcopy(figure)
    updated.setdefault("layout", {})
    updated["layout"].setdefault("xaxis", {})
    updated["layout"]["xaxis"]["range"] = [
        new_start.isoformat(),
        new_end.isoformat(),
    ]
    updated["layout"]["uirevision"] = "overview-graph"
    return updated
