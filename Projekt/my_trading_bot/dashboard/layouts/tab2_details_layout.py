# ==================== dashboard/layouts/tab2_details_layout.py ====================

from dash import html, dcc
from dashboard.data_loader import get_available_results

results = get_available_results()
symbols = sorted(set([res[0] for res in results]))
strategies = sorted(set([res[1] for res in results]))

layout = html.Div([
    html.H2("Strategiedetails"),
    html.Div([
        html.Label("Wähle eine Strategie:"),
        dcc.Dropdown(id="details-strategy-dropdown", options=[{"label": s, "value": s} for s in strategies], multi=False)
    ]),
    html.Div([
        html.Label("Wähle ein Symbol:"),
        dcc.Dropdown(id="details-symbol-dropdown", options=[{"label": s, "value": s} for s in symbols], multi=False)
    ]),
    html.Div(id="quantstats-metrics"),
    dcc.Graph(id="quantstats-performance-graph")
])
