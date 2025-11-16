from dash import dcc, html

layout = html.Div(
    className="tab-container",
    children=[
        html.H2("Strategiedetails", className="tab-heading"),
        dcc.Interval(id="details-options-refresh", interval=20_000, n_intervals=0),
        html.Div(
            className="control-row",
            children=[
                html.Div(
                    className="control-group",
                    children=[
                        html.Label("Wähle eine Strategie", className="control-label"),
                        dcc.Dropdown(
                            id="details-strategy-dropdown",
                            options=[],
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
