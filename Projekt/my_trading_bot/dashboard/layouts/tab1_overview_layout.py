from dash import dcc, html

from dashboard.data_loader import get_available_results


results = get_available_results()
symbols = sorted({symbol for symbol, _ in results})
strategies = sorted({strategy for _, strategy in results})


layout = html.Div(
    className="tab-container",
    children=[
        html.H2("Übersicht & Vergleich", className="tab-heading"),
        html.Div(
            className="control-row",
            children=[
                html.Div(
                    className="control-group",
                    children=[
                        html.Label("Wähle Symbole", className="control-label"),
                        dcc.Dropdown(
                            id="overview-symbol-dropdown",
                            options=[{"label": sym, "value": sym} for sym in symbols],
                            multi=True,
                            placeholder="Symbole auswählen",
                        ),
                    ],
                ),
                html.Div(
                    className="control-group",
                    children=[
                        html.Label("Wähle Strategien", className="control-label"),
                        dcc.Dropdown(
                            id="overview-strategy-dropdown",
                            options=[{"label": strat, "value": strat} for strat in strategies],
                            multi=True,
                            placeholder="Strategien auswählen",
                        ),
                    ],
                ),
            ],
        ),
        dcc.Loading(
            type="circle",
            className="loading-overlay",
            children=[
                html.Div(id="performance-table", className="card"),
                html.Div(
                    className="card",
                    children=dcc.Graph(
                        id="overview-comparison-graph",
                        config={"displayModeBar": False},
                    ),
                ),
            ],
        ),
    ],
)
