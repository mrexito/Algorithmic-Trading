from dash import dcc, html

from dashboard.data_loader import get_strategy_symbol_map


strategy_symbol_map = get_strategy_symbol_map()
strategy_options = sorted(strategy_symbol_map.keys())


layout = html.Div(
    className="tab-container",
    children=[
        html.H2("Strategiedetails", className="tab-heading"),
        html.Div(
            className="control-row",
            children=[
                html.Div(
                    className="control-group",
                    children=[
                        html.Label("Wähle eine Strategie", className="control-label"),
                        dcc.Dropdown(
                            id="details-strategy-dropdown",
                            options=[{"label": s, "value": s} for s in strategy_options],
                            placeholder="Strategie auswählen",
                            clearable=True,
                        ),
                    ],
                ),
                html.Div(
                    className="control-group",
                    children=[
                        html.Label("Wähle ein Symbol", className="control-label"),
                        dcc.Dropdown(
                            id="details-symbol-dropdown",
                            options=[],
                            placeholder="Symbol auswählen",
                            clearable=True,
                            disabled=True,
                        ),
                    ],
                ),
            ],
        ),
        dcc.Loading(
            type="circle",
            className="card",
            children=html.Div(
                id="quantstats-report",
                className="quantstats-report",
            ),
        ),
    ],
)
