# ==================== dashboard/layouts/tab2_details_layout.py ====================
"""Layout for the detail tab with dropdown filters and QuantStats placeholders."""

from dash import html, dcc
from dashboard.data_loader import get_available_results

results = get_available_results()
symbols = sorted(set([res[0] for res in results]))
strategies = sorted(set([res[1] for res in results]))

layout = html.Div([
    html.H2("Strategiedetails"),

    html.Div([
        html.Label("Wähle eine Strategie:"),
        dcc.Dropdown(
            id="details-strategy-dropdown",
            options=[{"label": s, "value": s} for s in strategies],
            placeholder="Strategie auswählen...",
            clearable=True,
            style={"width": "50%"}
        ),
    ], style={"marginBottom": "16px"}),

    html.Div([
        html.Label("Wähle ein Symbol:"),
        dcc.Dropdown(
            id="details-symbol-dropdown",
            options=[{"label": s, "value": s} for s in symbols],
            placeholder="Symbol auswählen...",
            clearable=True,
            style={"width": "50%"}
        ),
    ], style={"marginBottom": "24px"}),

    html.Div(id="quantstats-metrics", style={"marginBottom": "40px"}),

    html.Div(
        id="quantstats-report",
        style={
            "borderTop": "1px solid #ccc",
            "paddingTop": "20px",
            "maxHeight": "1600px",
            "overflowY": "auto"
        }
    ),
])
