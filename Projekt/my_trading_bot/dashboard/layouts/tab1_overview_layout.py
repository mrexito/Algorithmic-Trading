"""Layout for the overview tab that compares strategies across symbols."""

from dash import html, dcc
from dashboard.data_loader import get_available_results

results = get_available_results()
symbols = sorted(set([res[0] for res in results]))
strategies = sorted(set([res[1] for res in results]))

layout = html.Div(
    [
        dcc.Store(id="bootstrap-requested-symbols"),
        dcc.Store(id="bootstrap-reload-store"),
        html.Div(id="bootstrap-reload-dummy", style={"display": "none"}),
        html.H2("Übersicht & Vergleich"),
        html.Div(
            [
                html.Label("Neue Symbole laden:"),
                dcc.Input(
                    id="bootstrap-symbol-input",
                    type="text",
                    placeholder="z.B. MSFT, AMZN",
                    style={"marginRight": "8px", "width": "220px"},
                ),
                html.Button("Daten laden", id="bootstrap-symbol-button", n_clicks=0),
                html.Span(
                    id="bootstrap-symbol-message",
                    style={"marginLeft": "12px", "fontStyle": "italic"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "marginBottom": "12px"},
        ),
        html.Div(
            [
                html.Label("Wähle Symbole:"),
                dcc.Dropdown(
                    id="overview-symbol-dropdown",
                    options=[{"label": sym, "value": sym} for sym in symbols],
                    multi=True,
                ),
            ]
        ),
        html.Div(
            [
                html.Label("Wähle Strategien:"),
                dcc.Dropdown(
                    id="overview-strategy-dropdown",
                    options=[{"label": strat, "value": strat} for strat in strategies],
                    multi=True,
                ),
            ]
        ),
        html.Div(id="performance-table"),
        dcc.Graph(id="overview-comparison-graph"),
    ]
)
