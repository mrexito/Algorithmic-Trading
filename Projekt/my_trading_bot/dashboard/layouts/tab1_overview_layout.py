"""Layout for the overview tab that compares strategies across symbols."""

from dash import html, dcc
from dashboard.data_loader import get_available_results

results = get_available_results()
symbols = sorted(set([res[0] for res in results]))
strategies = sorted(set([res[1] for res in results]))

layout = html.Div([
    html.H2("Übersicht & Vergleich"),
    html.Div([
        html.Label("Wähle Symbole:"),
        dcc.Dropdown(id="overview-symbol-dropdown", options=[{"label": sym, "value": sym} for sym in symbols], multi=True)
    ]),
    html.Div([
        html.Label("Wähle Strategien:"),
        dcc.Dropdown(id="overview-strategy-dropdown", options=[{"label": strat, "value": strat} for strat in strategies], multi=True)
    ]),
    html.Div(id="performance-table"),
    dcc.Graph(id="overview-comparison-graph")
])
