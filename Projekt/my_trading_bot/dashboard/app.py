"""Dash application entry point wiring layouts and callbacks together."""

import os
import sys

import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Allow running the script directly (python dashboard/app.py) by making sure the package root is on sys.path.
if __package__ in (None, ""):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from dashboard.layouts import (
    tab1_overview_layout,
    tab2_details_layout,
    tab3_descriptions_layout,
)
from dashboard.data_loader import schedule_bootstrap

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Trading Dashboard"

app.layout = html.Div(
    [
        html.Div(
            [
                html.Span("Data source: ", style={"opacity": 0.7, "marginRight": "4px"}),
                html.Span(id="backend-status", style={"fontWeight": "600"}),
                dcc.Interval(id="backend-status-ivl", interval=30_000, n_intervals=0),
            ],
            style={
                "display": "flex",
                "justifyContent": "flex-end",
                "gap": "4px",
                "padding": "6px 8px",
                "fontSize": "12px",
                "color": "#444",
                "borderBottom": "1px solid #eee",
            },
        ),
        dcc.Tabs(
            id="tabs",
            value="tab1",
            children=[
                dcc.Tab(label="Übersicht & Vergleich", value="tab1"),
                dcc.Tab(label="Strategiedetails", value="tab2"),
                dcc.Tab(label="Strategiebeschreibungen", value="tab3"),
            ],
        ),
        html.Div(id="tabs-content"),
    ]
)


@app.callback(
    dash.dependencies.Output("tabs-content", "children"),
    [dash.dependencies.Input("tabs", "value")],
)
def render_tab_content(tab):
    """Return the layout for the currently selected dashboard tab."""
    if tab == "tab1":
        return tab1_overview_layout.layout
    elif tab == "tab2":
        return tab2_details_layout.layout
    elif tab == "tab3":
        return tab3_descriptions_layout.layout


# Backend status updater
@app.callback(
    dash.dependencies.Output("backend-status", "children"),
    dash.dependencies.Input("backend-status-ivl", "n_intervals"),
)
def update_backend_status(_):
    """Show whether TimescaleDB or cached CSV data is currently reachable."""
    # Import here to avoid circular imports at app startup
    from dashboard.data_loader import get_backend_status
    return get_backend_status()

app.clientside_callback(
    """
    function(ts){
        if(ts){
            window.location.reload();
        }
        return "";
    }
    """,
    Output("bootstrap-reload-dummy", "children"),
    Input("bootstrap-reload-store", "data"),
    prevent_initial_call=True,
)

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") in (None, "true"):
        schedule_bootstrap()
    from dashboard.callbacks import (
        tab1_overview_callbacks,
        tab2_details_callbacks,
        tab3_descriptions_callbacks,
    )

    app.run(debug=True)
