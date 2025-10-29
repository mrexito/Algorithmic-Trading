import dash
import numpy as np
import plotly.graph_objs as go
import quantstats.stats as qs_stats
from dash import dash_table, html
from dash.dependencies import Input, Output

from dashboard.data_loader import load_returns, normalize_returns


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
)
def update_overview_tab(selected_symbols, selected_strategies):
    if not selected_symbols or not selected_strategies:
        return dash.no_update, dash.no_update

    table_rows = []
    figure = go.Figure()

    for symbol in selected_symbols:
        for strategy in selected_strategies:
            raw_returns = load_returns(symbol, strategy)
            returns = normalize_returns(raw_returns)
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
    )

    return performance_table, figure
